#!/usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import treetaggerwrapper, re, nltk, logging, json, utils, locale, calendar, datetime
from pprint import pprint
from pymongo import MongoClient
from bson import ObjectId

# Custom file
from support_object import *

# Custom class importer
from DayManager import DayManager
from PoolManager import PoolManager
from ProposeManager import ProposeManager

daymanager = DayManager()
poolmanager = PoolManager()
proposemanager = ProposeManager()

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
    new_pool = poolmanager.init_pool()

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
                
                # This word is a day_transformers! Set new pool day ad +1/+2 on today timestamp.
                if tags[index].pos.startswith("ADV") and tags[index].word in day_transformers:
                    default_value = False
                    new_pool['time_value']['pool_day'] = week_days[ (datetime.datetime.now() + datetime.timedelta( days=day_transformers[tags[index].word] )).weekday() ]
                    continue

                if tags[index].pos.startswith(("VER", "NOM")):

                    if tags[index].pos.startswith("NOM"):

                        # This word is a day! Set pool_day and ignore the following code.
                        is_day = daymanager.is_day(tags[index].word)
                        if is_day != -1:
                            new_pool['time_value']['pool_day'] = daymanager.get_day(index=is_day)
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
                    
                    if tags[index].lemma not in ["andare", "avere"] and propose is None:
                        if index+1 < len(tags):
                            if tags[index+1].pos.startswith("NOM") and not tags[index].pos.startswith("NOM") and utils.is_day(tags[index].word, week_days) != -1 :
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

    day_to_add = daymanager.day_to_add(datetime.datetime.now(), new_pool['time_value']['pool_day'])
    new_pool['time_value']['close_datetime'] = daymanager.get_close_pool( daymanager.add_day(day_to_add), time_pointers[new_pool['time_value']['time_pointers']] )
    
    # There is another pool open in the same day?
    if new_pool['title'] != None and poolmanager.pools_same_day(update.message.chat_id, new_pool['time_value']) is None:
            utils.create_new_pool(new_pool, proposals, update.message, bot, database)
    elif proposals != []:
        opened_pool = poolmanager.get_opened_pools(update.message.chat_id)
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
                _id = proposemanager.new_propose(pending_propose)
                question_pool_message = update.message.reply_text("Scusami a quale sondaggio ti riferisci?", reply_markup=utils.ask_pool(pending_propose))
                proposemanager.update_propose(_id, {"message_id": question_pool_message.message_id} )

def button(bot, update):
    query = update.callback_query
    callback_data = json.loads(query.data)
    if callback_data[utils.STRUCT_CALLBACK['TYPE']] == utils.BUTTON_TYPE['VOTE']:
        pool = poolmanager.get_pool(callback_data[utils.STRUCT_CALLBACK['ID']])
        if query.from_user.id not in pool['proposals'][callback_data[utils.STRUCT_CALLBACK['INDEX']]]['voted_by']: 
            pool['proposals'][callback_data[utils.STRUCT_CALLBACK['INDEX']]]['voted_by'].append(query.from_user.id)
            bot.edit_message_text(
                pool['title'], 
                chat_id=query.message.chat.id, 
                message_id=pool['message_id'], 
                reply_markup=utils.render_keyboard( pool )
            )
            poolmanager.update_pool(pool['_id'], {'proposals': pool["proposals"]})
    elif callback_data[utils.STRUCT_CALLBACK['TYPE']] == utils.BUTTON_TYPE['CLOSE']:
        pool = poolmanager.get_pool(callback_data[utils.STRUCT_CALLBACK['ID']])
        handle_close_pool(pool, bot)
    elif callback_data[utils.STRUCT_CALLBACK['TYPE']] == utils.BUTTON_TYPE['CHOICE']:
        pending_propose = proposemanager.get_propose(callback_data[utils.STRUCT_CALLBACK['ID']])
        if query.from_user.id == pending_propose['from_user']:
            pool = poolmanager.get_pool(pending_propose['pools'][callback_data[utils.STRUCT_CALLBACK['INDEX']]]['_id'] )
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
    poolmanager.update_pool(pool['_id'], {'closed': True})
    
# Quale pool vuoi chiudere?
def close_pool(bot, update):
    opened_pool = poolmanager.get_opened_pools(update.message.chat_id, owner=update.message.from_user.id)
    if opened_pool == []:
        update.message.reply_text('Non hai sondaggi aperti in questo gruppo!')
    elif len(opened_pool) == 1:
        handle_close_pool(opened_pool[0], bot)
    else:
        update.message.reply_text("Sembra ci siano più sondaggi aperti. A quale ti riferisci?", reply_markup=utils.pools_to_close(opened_pool))

def tick_pool(bot, job):
    pools = poolmanager.get_pools_toclose(job.context)
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