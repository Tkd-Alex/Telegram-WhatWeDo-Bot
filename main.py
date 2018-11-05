#!/usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import treetaggerwrapper, re, nltk, logging, json, utils, locale, calendar, datetime
from pprint import pprint
from pymongo import MongoClient
from bson import ObjectId

# Telegram import 
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity

with open('settings.json') as f:
    settings = json.load(f)

token = settings['telegram_token']

tagger = treetaggerwrapper.TreeTagger(TAGLANG='it', TAGDIR='./TreeTagger', TAGPARFILE='./TreeTagger/lib/italian.par')

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - [%(funcName)s]: %(message)s', datefmt='%d/%m/%Y %H:%M:%S', level=logging.INFO)
logger = logging.getLogger('MAIN')

nltk.download('punkt')

client = MongoClient()
database = client['pool_group']

calendar.setfirstweekday(calendar.MONDAY)
locale.setlocale(locale.LC_ALL, 'it_IT.utf8')

week_days = list( calendar.day_name )

means_of_transport = [ p.rstrip() for p in open("mezzi_di_trasporto.txt","r").readlines() ]

day_transformers = {
    "domani": 1,
    "dopodomani": 2
}

time_pointers = {
    "stasera": 20,
    "sera": 20,
    "pranzo": 13,
    "cena": 21,
    "colazione": 8,
    "oggi": 0
}

prepositions = {
    "di":       False, # a casa di alex (?)
    "del":      False,
    "dello":    False,
    "della":    False,
    "dei":      False,
    "degli":    False,
    "delle":    False,
    
    "a":        True, # a piedi? (solved with dict)
    "al":       True,
    "allo":     True,
    "alla":     True,
    "ai":       False,
    "agli":     False,
    "alle":     False,

    "da":       False,
    "dal":      False,
    "dallo":    False,
    "dalla":    False,
    "dai":      False,
    "dagli":    False,
    "dalle":    False,

    "in":       True, # in auto? (solved with dict)
    "nel":      False,
    "nello":    False,
    "nella":    False,
    "nei":      False,
    "negli":    False,
    "nelle":    False,

    "con":      False,

    "su":       False,
    "sul":      False,
    "sullo":    False,
    "sulla":    False,
    "sui":      False,
    "sugli":    False,
    "sulle":    False,

    "per":      False,

    "tra":      False,

    "fra":      False
}

# Controllare per ogni sentenza se:
# 1 - È una nuova proposta, dunque non esiste un altro pool relativo allo stesso giorno e stesso orario di chiusura.
# 2 - Se è una risposta al pool capire a quale pool associarlo:
#   -   Se nella risposta vi sono parole chiave con giorno o puntatore temporale.
#   -   Se nella risposta non ci sono parole chiave:
#       -   Con multipli pool aperti chiedere a quale ci si riferisce.
#       -   Con un solo pool aperto associarlo direttamente ad esso.
def analyzes_message(bot, update):
    # Create multiple sentences by message. nltk maybe split by '.'.
    sentences = nltk.sent_tokenize( update.message.text.lower() )

    proposals = []
    
    default_value = True
    new_pool = { 
        "title": None, 
        "closed": False, 
        "time_value": {
            "close_datetime": utils.get_close_pool( (datetime.datetime.now() + datetime.timedelta( days=1 ) ) ),
            "pool_day": week_days[datetime.datetime.now().weekday()],
            "time_pointers": "oggi"
        }
    } 
    
    # Iterate sentence.
    for sentence in sentences:
        # Create an array of word already tagged from [i] sentence
        tags_encoded = tagger.tag_text( sentence )
        tags = treetaggerwrapper.make_tags( tags_encoded )

        # Count all negation in the sentence. If is even skip sentence.
        negations = [ w.word for w in tags if w.word in [ 'non' ] ]

        if len(negations) % 2 == 0:
            middle = { 'index': -1, 'status': False }
            for index in range(0, len(tags)):
                print(tags[index])
                
                # This word is a day_transformers! Set new pool day ad +1/+2 on today timestamp.
                if tags[index].pos.startswith("ADV") and tags[index].word in day_transformers:
                    default_value = False
                    new_pool['time_value']['pool_day'] = week_days[ (datetime.datetime.now() + datetime.timedelta( days=day_transformers[tags[index].word] )).weekday() ]
                    continue

                if tags[index].pos.startswith(("VER", "NOM")):

                    if tags[index].pos.startswith("NOM"):

                        # This word is a day! Set pool_day and ignore the following code.
                        is_day = utils.is_day(tags[index].word, week_days)
                        if is_day != -1:
                            new_pool['time_value']['pool_day'] = week_days[is_day]
                            continue

                        # This word is a time pointers like ["pranzo", "cena"]. Set close pool by tome_pointers value.
                        if tags[index].word in time_pointers:
                            default_value = False
                            new_pool['time_value']['time_pointers'] = tags[index].word
                            continue

                        # This word is a mean of transport! Ignore the following code.
                        if tags[index].word in means_of_transport: 
                            continue

                    propose = None
                    
                    if utils.good_middle(middle, tags) is True:
                        if not(tags[middle['index']-1].lemma == "andare" and tags[index].pos.startswith("VER")):
                            propose = "{} {} {}".format(tags[middle['index']-1].word, tags[middle['index']].word, tags[index].word)
                    
                    if tags[index].lemma != "andare" and propose is None:
                        if index+1 < len(tags):
                            if tags[index+1].pos.startswith("NOM") and not tags[index].pos.startswith("NOM"):
                                propose = "{} {}".format(tags[index].word, tags[index+1].word)
                        elif not tags[index].pos.startswith("NOM"):
                            propose = tags[index].word

                    if propose != None and propose not in proposals:
                        proposals.append(propose)
                
                if tags[index].pos.startswith("VER") and tags[index].lemma in [ 'andare', 'fare' ] and '?' in sentence:
                    new_pool['title'] = update.message.text

                # Foundend preposition maybe the next word is a 'place' or 'action to do'
                if tags[index].pos.startswith("DET") or (tags[index].pos.startswith("PRE") and tags[index].lemma in prepositions and prepositions[tags[index].lemma] is True):
                    middle['status'] = True 
                    middle['index'] = index
                else:
                    middle = { 'index': -1, 'status': False }

    day_to_add = utils.day_to_add(datetime.datetime.now(), new_pool['time_value']['pool_day'], week_days )
    new_pool['time_value']['close_datetime'] = utils.get_close_pool( (datetime.datetime.now() + datetime.timedelta( day_to_add ) ), time_pointers[new_pool['time_value']['time_pointers']] )                        

    # There is another pool open in the same day?
    if new_pool['title'] != None and database.pool.find_one({
            "chat_id": update.message.chat_id, 
            "closed": False, 
            "time_value.pool_day": new_pool['time_value']['pool_day'], 
            "time_value.time_pointers": new_pool['time_value']['time_pointers']
        }) is None:
            utils.create_new_pool(new_pool, proposals, update.message, bot, database)
    elif proposals != []:
        opened_pool = database.pool.find({"chat_id": update.message.chat_id, "closed": False})
        opened_pool = list(opened_pool)
        if len(opened_pool) == 1:
            utils.update_propose(opened_pool[0], proposals, update.message.chat_id, bot, database)
        elif len(opened_pool) > 1:
            pools = [ 
                p for p in opened_pool 
                if p['time_value']['pool_day'] == new_pool['time_value']['pool_day'] 
                and p['time_value']['time_pointers'] == new_pool['time_value']['time_pointers'] 
            ]
            if len(pools) == 1 and default_value is False: # I'm sure this is the right pool
                utils.update_propose(pools[0], proposals, update.message.chat_id, bot, database)
            else:
                pending_propose = {
                    "pools": [ {"title": p['title'], "_id": p['_id']} for p in opened_pool ],
                    "proposals": proposals, 
                    "from_user": update.message.from_user.id,
                }
                database.pending_propose.insert_one( pending_propose )
                question_pool_message = update.message.reply_text("Scusami a quale sondaggio ti riferisci?", reply_markup=utils.ask_pool(pending_propose))
                database.pending_propose.update_one({"_id": pending_propose['_id']}, {"$set": {"message_id": question_pool_message.message_id} })

def button(bot, update):
    query = update.callback_query
    callback_data = json.loads(query.data)
    if callback_data[utils.STRUCT_CALLBACK['TYPE']] == utils.BUTTON_TYPE['VOTE']:
        pool = database.pool.find_one({"_id": ObjectId(callback_data[utils.STRUCT_CALLBACK['ID']])})
        if query.from_user.id not in pool['proposals'][callback_data[utils.STRUCT_CALLBACK['INDEX']]]['voted_by']: 
            pool['proposals'][callback_data[utils.STRUCT_CALLBACK['INDEX']]]['voted_by'].append(query.from_user.id)

            bot.edit_message_text(
                pool['title'], 
                chat_id=query.message.chat.id, 
                message_id=pool['message_id'], 
                reply_markup=utils.render_keyboard( pool )
            )
            database.pool.update_one({"_id": pool['_id']}, {"$set": {'proposals': pool["proposals"]} })
    elif callback_data[utils.STRUCT_CALLBACK['TYPE']] == utils.BUTTON_TYPE['CHOICE']:
        pending_propose = database.pending_propose.find_one({"_id": ObjectId(callback_data[utils.STRUCT_CALLBACK['ID']])})
        if query.from_user.id == pending_propose['from_user']:
            pool = database.pool.find_one({"_id": ObjectId( pending_propose['pools'][callback_data[utils.STRUCT_CALLBACK['INDEX']]]['_id'] )})
            utils.update_propose(pool, pending_propose['proposals'], query.message.chat.id, bot, database)
            bot.delete_message(query.message.chat.id, pending_propose['message_id'])

def handle_close_pool(pool, bot):
    close_message = "Il sondaggio: <i>{}</i>\nè stato chiuso!\n\n".format(pool['title'])
    sorted_proposals = sorted(pool['proposals'], key=lambda item: len(item['voted_by']), reverse=True)
    winners = [ w for w in sorted_proposals if len(sorted_proposals[0]['voted_by']) ==  len(w['voted_by']) ]
    if len(winners) == 1:
        close_message += "Ha vinto: <i>{}</i> , con <b>{}</b> {}!".format(winners[0]['propose'], len(winners[0]['voted_by']), "voti" if len(winners[0]['voted_by']) > 1 else "voto" )
    else:
        close_message += "Con <b>{}</b> {} vincono:\n".format(len(winners[0]['voted_by']), "voti" if len(winners[0]['voted_by']) > 1 else "voto")
        for winner in winners:
            close_message += "- <i>{}</i>\n".format(winner['propose'].capitalize())

    bot.send_message(pool['chat_id'], close_message, parse_mode="HTML")
    database.pool.update_one({"_id": pool['_id']}, {"$set": {'closed': True}} )

def close_pool(bot, update):
    pool = database.pool.find_one({"chat_id": update.message.chat_id, "closed": False, "owner": update.message.from_user.id})
    if pool is None:
        update.message.reply_text('Non hai sondaggi aperti in questo gruppo!')
    else:
        handle_close_pool(pool, bot)

def tick_pool(bot, job):
    pools = database.pool.find({
        "time_value.time_pointers": job.context,
        "time_value.pool_day": week_days[datetime.datetime.now().weekday()], # Force database params. Not necessary.
        "time_value.close_datetime": utils.get_close_pool(datetime.datetime.now(), time_pointers[job.context])
    })
    pools = list(pools)
    for pool in pools:
        handle_close_pool(pool, bot)

def error(bot, update, error):
    logger.error('Update "%s" caused error "%s"' % (update, error))
                     
if __name__ == '__main__':
    updater = Updater(token, request_kwargs={'read_timeout': 20, 'connect_timeout': 20})
    dp = updater.dispatcher
    job = updater.job_queue
    for pointer in time_pointers:
        job.run_daily(
            tick_pool, 
            datetime.time(time_pointers[pointer], 00, 00), 
            context=pointer,
            name='POOL TICK {}:00 - {}'.format(time_pointers[pointer], pointer.capitalize())
        )
    dp.add_handler(CommandHandler("close_pool", close_pool))
    dp.add_handler(MessageHandler(Filters.text, analyzes_message))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_error_handler(error)
    updater.start_polling(timeout=25)
    updater.idle()