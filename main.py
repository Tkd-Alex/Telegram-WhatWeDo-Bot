#!/usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import treetaggerwrapper, re, nltk, logging, json, utils
from pprint import pprint
from pymongo import MongoClient

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
database = client[ 'word_analysis' ]

proposes = [ 'andare', 'fare' ]
proposes += utils.get_synonymous(database, 'andare')
proposes += utils.get_synonymous(database, 'fare')

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

def analyzes_message(bot, update, chat_data):
    # Create chat data array sentence
    if "sentence" not in chat_data:
        chat_data["sentence"] = []

    sentences = nltk.sent_tokenize( update.message.text.lower() )
    proposals = []
    title_proposes = None
    for sentence in sentences:
        tags_encoded = tagger.tag_text( sentence )
        tags = treetaggerwrapper.make_tags( tags_encoded )

        is_negate = False
        preposition_before = False
        for tag in tags:

            if tag.word in negation:
                is_negate = True

            if tag.pos.startswith(("VER", "NOM")) and preposition_before is True:
                if tag.word not in proposals:
                    proposals.append(tag.word)
            
            if tag.pos.startswith("VER") and tag.lemma in proposes and is_negate is False:
                title_proposes = sentence.capitalize()

            # Foundend preposition maybe the next word is a 'place' or 'action to do'
            # Anzichè escludere DI conviene includere solo A
            preposition_before = True if tag.pos.startswith("PRE") and tag.word != 'di' and not tag.word in preposition['di'] else False
    
    if [ a for a in chat_data["sentence"] if a['closed'] is False ] == []:
        if title_proposes != None:
            
            keyboard = [ [] ]
            for index in range(0, len(proposals)):
                if len(keyboard[len(keyboard)-1]) == 3:
                    keyboard.append([])
                
                keyboard[len(keyboard)-1].append( InlineKeyboardButton(proposals[index].capitalize(), callback_data=str(index+1)) )
    
            reply_markup = InlineKeyboardMarkup(keyboard)
            new_sentence = bot.send_message(update.message.chat_id, title_proposes, reply_markup=reply_markup)
            chat_data["sentence"].append({
                    "message_id": new_sentence.message_id,
                    "title": title_proposes,
                    "closed": False,
                    "proposals": [ {"propose": p, "vote": 0 } for p in proposals ]
                }
            )
    else:
        # Foundend open sentence add proposals:
        if proposals != []:
            last_sentence = chat_data["sentence"][len(chat_data["sentence"])-1]
            old_proposals = last_sentence["proposals"]
            for propose in proposals:
                if propose not in [ p['propose'] for p in old_proposals ]:
                    last_sentence["proposals"].append({
                        "propose": propose, 
                        "vote": 0
                    })

            keyboard = [ [] ]
            proposals = last_sentence["proposals"]
            for index in range(0, len(proposals)):
                if len(keyboard[len(keyboard)-1]) == 3:
                    keyboard.append([])
                
                keyboard[len(keyboard)-1].append(
                    InlineKeyboardButton(proposals[index]["propose"].capitalize(), 
                    callback_data=str(index+1)) 
                )
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(
                last_sentence['title'], 
                chat_id=update.message.chat_id, 
                message_id=last_sentence['message_id'], 
                reply_markup=reply_markup
            )

def error(bot, update, error):
    logger.error('Update "%s" caused error "%s"' % (update, error))
                     
if __name__ == '__main__':
    updater = Updater(token, request_kwargs={'read_timeout': 20, 'connect_timeout': 20})
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text, analyzes_message, pass_chat_data=True))
    dp.add_error_handler(error)
    updater.start_polling(timeout=25)
    updater.idle()