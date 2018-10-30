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
database = client[ 'pool_group' ]

calendar.setfirstweekday(calendar.MONDAY)
locale.setlocale(locale.LC_ALL, 'it_IT.utf8')

week_days = list( calendar.day_name )

means_of_transport = [ p.rstrip() for p in open("mezzi_di_trasporto.txt","r").readlines() ]

# stasera, domani, a pranzo, a cena, dopodomani

time_transformers = {
    "domani": 1,
    "dopodomani": 2
}

time_pointers = {
    "stasera": 20,
    "sera": 20,
    "pranzo": 13,
    "cena": 21,
    "colazione": 8
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

def analyzes_message(bot, update):
    sentences = nltk.sent_tokenize( update.message.text.lower() )
    proposals = []
    
    # Default pool day = TODAY
    new_pool = { 
        "title": None, 
        "closed": False, 
        "time_value": {
            "close_datetime": utils.get_close_pool( (datetime.datetime.now() + datetime.timedelta( days=1 ) ) ),
            "pool_day": week_days[datetime.datetime.now().weekday()],
            "time_pointers": None
        }
    } 
    
    for sentence in sentences:
        tags_encoded = tagger.tag_text( sentence )
        tags = treetaggerwrapper.make_tags( tags_encoded )

        negations = [ w.word for w in tags if w.word in [ 'non' ] ]

        if len(negations) % 2 == 0:
            middle = { 'index': -1, 'status': False }
            for index in range(0, len(tags)):
                print(tags[index])

                if tags[index].pos.startswith(("VER", "NOM")):

                    if tags[index].pos.startswith("NOM"):
                        # This word is a day! Set pool_day and ignore the following code.
                        is_day = utils.is_day(tags[index].word, week_days)
                        if is_day != -1:
                            new_pool['time_value']['pool_day'] = week_days[is_day]
                            continue

                        # This word is a time_transformers! Set new pool day ad +1/+2 on today timestamp.
                        if tags[index].word in time_transformers:
                            new_pool['time_value']['pool_day'] = week_days[ (datetime.datetime.now() + datetime.timedelta( days=time_transformers[tags[index].word] )).weekday() ]
                            continue

                        if tags[index].word in time_pointers:
                            day_to_add = utils.day_to_add(datetime.datetime.now(), new_pool['time_value']['pool_day'], week_days )
                            new_pool['time_value']['close_datetime'] = utils.get_close_pool( (datetime.datetime.now() + datetime.timedelta( day_to_add ) ), time_pointers[tags[index].word] )
                            new_pool['time_value']['time_pointers']: tags[index].words
                            continue

                        # This word is a mean of transport! Set pool_day and ignore the following code.
                        if tags[index].word in means_of_transport: 
                            continue

                    propose = None
                    
                    if utils.good_middle(middle, tags) is True:
                        if not(tags[middle['index']-1].lemma == "andare" and tags[index].pos.startswith("VER")):
                            propose = "{} {} {}".format(tags[middle['index']-1].word, tags[middle['index']].word, tags[index].word)
                    
                    if tags[index].lemma != "andare" and propose is None:
                        if index+1 < len(tags):
                            if tags[index+1].pos.startswith("NOM"):
                                propose = "{} {}".format(tags[index].word, tags[index+1].word)
                        elif not tags[index].pos.startswith("NOM"):
                            propose = tags[index].word

                    if propose != None and propose not in proposals:
                        proposals.append(propose)
                
                if tags[index].pos.startswith("VER") and tags[index].lemma in [ 'andare', 'fare' ]:
                    new_pool['title'] = update.message.text

                # Foundend preposition maybe the next word is a 'place' or 'action to do'
                if  tags[index].pos.startswith("DET") or (tags[index].pos.startswith("PRE") and tags[index].lemma in prepositions and prepositions[tags[index].lemma] is True):
                    middle['status'] = True 
                    middle['index'] = index
                else:
                    middle = { 'index': -1, 'status': False }

    # There is another pool open in the same day?

    # C'è comunque un problema quando si aggiunge una proposa e ovviamente non è stato specificato il pool_day
    last_pool = database.pool.find_one({"chat_id": update.message.chat_id, "closed": False, "time_value.pool_day": new_pool['time_value']['pool_day'], "time_value.time_pointers": new_pool['time_value']['time_pointers']})
    if last_pool is None:
        if new_pool['title'] != None:
            new_pool["owner"] = update.message.from_user.id,
            new_pool["chat_id"] = update.message.chat_id,
            new_pool["proposals"] = [ { "propose": p, "voted_by": [] } for p in proposals ]
        
            database.pool.insert_one( new_pool )

            new_pool_message = bot.send_message(update.message.chat_id, new_pool['title'], reply_markup=utils.render_keyboard( new_pool ))
            database.pool.update_one({"_id": new_pool['_id']}, {"$set": {"message_id": new_pool_message.message_id} })
    else:
        # Foundend open pool and new proposals to add:
        if [ p['propose'] for p in last_pool["proposals"] if p['propose'] in proposals]  != proposals:
            for propose in proposals:
                if propose not in [ p['propose'] for p in last_pool["proposals"] ]:
                    last_pool["proposals"].append({
                        "propose": propose, 
                        "voted_by": []
                    })
            
            database.pool.update_one({"_id": last_pool['_id']}, {"$set": {'proposals': last_pool["proposals"]} })
            bot.edit_message_text(
                last_pool['title'], 
                chat_id=update.message.chat_id, 
                message_id=last_pool['message_id'], 
                reply_markup=utils.render_keyboard( last_pool )
            )

def button(bot, update):
    query = update.callback_query
    callback_data = json.loads(query.data)
    pool = database.pool.find_one({"_id": ObjectId(callback_data['pool_id'])})
    if query.from_user.id not in pool['proposals'][callback_data['index']]['voted_by']: 
        pool['proposals'][callback_data['index']]['voted_by'].append(query.from_user.id)

        bot.edit_message_text(
            pool['title'], 
            chat_id=query.message.chat.id, 
            message_id=pool['message_id'], 
            reply_markup=utils.render_keyboard( pool )
        )
        database.pool.update_one({"_id": pool['_id']}, {"$set": {'proposals': pool["proposals"]} })

def close_pool(bot, update):
    pool = database.pool.find_one({"chat_id": update.message.chat_id, "closed": False, "owner": update.message.from_user.id})
    if pool is None:
        update.message.reply_text('Non hai sondaggi aperti in questo gruppo!')
    else:
        sorted_proposals = sorted(pool['proposals'], key=lambda item: len(item['voted_by']) , reversed=True)
        # Controllare i casi con parità
        winner, vote = sorted_proposals[0]['propose'], len(sorted_proposals[0]['voted_by'])
        update.message.reply_text('Sondaggio: {}\nChiuso!\n\nHa vinto: {}\nCon: {} voti!'.format(pool['title'], winner, vote ))
        database.pool.update_one({"_id": pool['_id']}, {"$set": {'closed': True}} )

def error(bot, update, error):
    logger.error('Update "%s" caused error "%s"' % (update, error))
                     
if __name__ == '__main__':
    updater = Updater(token, request_kwargs={'read_timeout': 20, 'connect_timeout': 20})
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("close_pool", close_pool))
    dp.add_handler(MessageHandler(Filters.text, analyzes_message))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_error_handler(error)
    updater.start_polling(timeout=25)
    updater.idle()