#!/usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import treetaggerwrapper, re, nltk, logging, json, utils
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

proposes = [ 'andare', 'fare' ]
# proposes += utils.get_synonymous(database, 'andare')
# proposes += utils.get_synonymous(database, 'fare')

negation = [ 'non' ]

preposition = {
    "di": [
        "del",
        "dello",
        "della",
        "dei",
        "degli",
        "delle",
    ]
}

# andiamo all'estero

# IO DIREI DI STUDIARE (NOT WORK)
def analyzes_message(bot, update):
    sentences = nltk.sent_tokenize( update.message.text.lower() )
    proposals = []
    pool_title = None
    for sentence in sentences:
        tags_encoded = tagger.tag_text( sentence )
        tags = treetaggerwrapper.make_tags( tags_encoded )

        negations = [ w.word for w in tags if w.word in negation ]
        if len(negations) % 2 == 0:
            middle = { 'index': -1, 'status': False }
            for index in range(0, len(tags)):
                print(tags[index])

                if tags[index].pos.startswith(("VER", "NOM")):
                    propose = None
                    
                    if utils.good_middle(middle, tags) is True:
                        if tags[middle['index']-1].lemma != "andare":
                            propose = "{} {} {}".format(tags[middle['index']-1].word, tags[middle['index']].word, tags[index].word)
                    
                    if tags[index].lemma not in proposes and propose is None:
                        if index+1 < len(tags):
                            if tags[index+1].pos.startswith("NOM"):
                                propose = "{} {}".format(tags[index].word, tags[index+1].word)
                        elif not tags[index].pos.startswith("NOM"):
                            propose = tags[index].word

                    if propose != None and propose not in proposals:
                        proposals.append(propose)
                
                if tags[index].pos.startswith("VER") and tags[index].lemma in proposes:
                    pool_title = update.message.text

                # Foundend preposition maybe the next word is a 'place' or 'action to do'
                # Anzichè escludere DI conviene includere solo A
                if tags[index].pos.startswith(("PRE", "DET")) and tags[index].word != 'di' and not tags[index].word in preposition['di']:
                    middle['status'] = True 
                    middle['index'] = index
                else:
                    middle = { 'index': -1, 'status': False }


    last_pool = database.pool.find_one({"chat_id": update.message.chat_id, "closed": False})
    if last_pool is None:
        if pool_title != None:
            keyboard = [ [] ]
            new_pool = {
                "owner": update.message.from_user.id,
                "chat_id": update.message.chat_id,
                "title": pool_title,
                "closed": False,
                "proposals": [ 
                    {
                        "propose": p, 
                        "voted_by": [] 
                    } for p in proposals ]
            }
            database.pool.insert_one( new_pool )
            
            for index in range(0, len(proposals)):
                if len(keyboard[len(keyboard)-1]) == 3:
                    keyboard.append([])

                callback_data = json.dumps({ 'index': index, 'pool_id': str(new_pool['_id']) })   
                keyboard[len(keyboard)-1].append( InlineKeyboardButton(proposals[index].capitalize(), callback_data=callback_data) )
    
            reply_markup = InlineKeyboardMarkup(keyboard)
            new_pool_message = bot.send_message(update.message.chat_id, pool_title, reply_markup=reply_markup)
            database.pool.update_one({"_id": new_pool['_id']}, {"$set": {"message_id": new_pool_message.message_id} })
    else:
        # Foundend open pool and new proposals to add:
        if proposals != []:
            for propose in proposals:
                if propose not in [ p['propose'] for p in last_pool["proposals"] ]:
                    last_pool["proposals"].append({
                        "propose": propose, 
                        "voted_by": []
                    })

            keyboard = [ [] ]
            for index in range(0, len(last_pool["proposals"])):
                if len(keyboard[len(keyboard)-1]) == 3:
                    keyboard.append([])
                
                callback_data = json.dumps({ 'index': index, 'pool_id': str(last_pool['_id']) })
                keyboard[len(keyboard)-1].append(
                    InlineKeyboardButton( 
                        "{} {}".format(
                            last_pool["proposals"][index]["propose"].capitalize(), 
                            "" if len(last_pool["proposals"][index]["voted_by"]) == 0 else "({})".format(len(last_pool["proposals"][index]["voted_by"])) 
                    ) , callback_data=callback_data ) 
                )
            
            database.pool.update_one({"_id": last_pool['_id']}, {"$set": {'proposals': last_pool["proposals"]} })
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(
                last_pool['title'], 
                chat_id=update.message.chat_id, 
                message_id=last_pool['message_id'], 
                reply_markup=reply_markup
            )

def button(bot, update):
    query = update.callback_query
    callback_data = json.loads(query.data)
    pool = database.pool.find_one({"_id": ObjectId(callback_data['pool_id'])})
    if query.from_user.id not in pool['proposals'][callback_data['index']]['voted_by']: 
        pool['proposals'][callback_data['index']]['voted_by'].append(query.from_user.id)
        keyboard = [ [] ]
        for index in range(0, len(pool['proposals'])):
            if len(keyboard[len(keyboard)-1]) == 3:
                keyboard.append([])
            
            callback_data = json.dumps({ 'index': index, 'pool_id': str(pool['_id']) })
            keyboard[len(keyboard)-1].append(
                InlineKeyboardButton( 
                    "{} {}".format(
                        pool['proposals'][index]["propose"].capitalize(), 
                        "" if len(pool['proposals'][index]["voted_by"]) == 0 else "({})".format(len(pool['proposals'][index]["voted_by"])) 
                ) , callback_data=callback_data ) 
            )
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(
            pool['title'], 
            chat_id=query.message.chat.id, 
            message_id=pool['message_id'], 
            reply_markup=reply_markup
        )
        database.pool.update_one({"_id": pool['_id']}, {"$set": {'proposals': pool["proposals"]} })

def close_pool(bot, update):
    pool = database.pool.find_one({"chat_id": update.message.chat_id, "closed": False, "owner": update.message.from_user.id})
    if pool is None:
        update.message.reply_text('Non hai sondaggi aperti in questo gruppo!')
    else:
        # Aggiungere chi ha vinto il sonaggio
        update.message.reply_text('Sondaggio: {}\nChiuso!'.format(pool['title']))
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