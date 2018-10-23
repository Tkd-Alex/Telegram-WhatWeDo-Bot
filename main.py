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

# Cosa facciamo stasera?
# Dove andiamo oggi?
# Io pensavo di andare al cinema
# Io voglio studiare programmazione
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
        middle = {
            'index': -1,
            'status': False
        }
        for index in range(0, len(tags)):

            if tags[index].word in negation:
                is_negate = True

            print(tags[index])
            if tags[index].pos.startswith(("VER", "NOM")) and utils.good_middle(middle, tags) is True:
                propose = None
                if tags[middle['index']-1].lemma != "andare":
                    propose = "{} {} {}".format(tags[middle['index']-1].word, tags[middle['index']].word, tags[index].word)
                elif tags[index].lemma != "fare":
                    propose = tags[index].word

                if propose != None and propose not in proposals:
                    proposals.append(propose)
            
            if tags[index].pos.startswith("VER") and tags[index].lemma in proposes and is_negate is False:
                # title_proposes = sentence.capitalize()
                title_proposes = update.message.text

            # Foundend preposition maybe the next word is a 'place' or 'action to do'
            # Anzichè escludere DI conviene includere solo A
            if tags[index].pos.startswith(("PRE", "DET")) and tags[index].word != 'di' and not tags[index].word in preposition['di']:
                middle['status'] = True 
                middle['index'] = index
     
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