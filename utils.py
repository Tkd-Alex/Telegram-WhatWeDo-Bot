#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json, datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

BUTTON_TYPE = {
    "CHOICE": 1,
    "VOTE": 2
}

STRUCT_CALLBACK = {
    "TYPE": "0",
    "INDEX": "1",
    "ID": "2"
}

def good_middle(middle, tags):
    if middle['index']-1 < 0:
        return False
    if middle['status'] is True and tags[middle['index']-1].pos.startswith("VER"):
        return True
    return False

def is_day(word, week_days):
    for index in range(0, len(week_days)):
        if word.startswith( week_days[index][:len(week_days)-1] ):
            return index
    return -1

def pools_to_close(pools):
    keyboard = [ ]
    for index in range(0, len(pools)):
        keyboard.append([])
        callback_data = json.dumps({ STRUCT_CALLBACK['TYPE']: BUTTON_TYPE['CLOSE'], STRUCT_CALLBACK['ID']: str(pools[index]['_id']) })
        keyboard[len(keyboard)-1].append( InlineKeyboardButton(pools[index]['title'] , callback_data=callback_data ))
    return InlineKeyboardMarkup(keyboard)

def ask_pool(pending_propose):
    keyboard = [ ]
    for index in range(0, len(pending_propose['pools'])):
        keyboard.append([])
        callback_data = json.dumps({ STRUCT_CALLBACK['TYPE']: BUTTON_TYPE['CHOICE'], STRUCT_CALLBACK['INDEX']: index, STRUCT_CALLBACK['ID']: str(pending_propose['_id']) })
        keyboard[len(keyboard)-1].append( InlineKeyboardButton(pending_propose['pools'][index]['title'] , callback_data=callback_data ))
    return InlineKeyboardMarkup(keyboard)

def render_keyboard(pool):
    keyboard = [ [] ]
    for index in range(0, len(pool["proposals"])):
        if len(keyboard[len(keyboard)-1]) == 3:
            keyboard.append([])

        callback_data = json.dumps({ STRUCT_CALLBACK['TYPE']: BUTTON_TYPE['VOTE'], STRUCT_CALLBACK['INDEX']: index, STRUCT_CALLBACK['ID']: str(pool['_id']) })
        keyboard[len(keyboard)-1].append(
            InlineKeyboardButton( 
                "{} {}".format(
                    pool["proposals"][index]["propose"].capitalize(), 
                    "" if len(pool["proposals"][index]["voted_by"]) == 0 else "({})".format(len(pool["proposals"][index]["voted_by"])) 
            ) , callback_data=callback_data ) 
        )

    return InlineKeyboardMarkup(keyboard)

def create_new_pool(pool, proposals, message, bot, database):
    pool["owner"] = message.from_user.id
    pool["chat_id"] = message.chat_id
    pool["proposals"] = [ { "propose": p, "voted_by": [] } for p in proposals ]
    
    database.pool.insert_one( pool )

    new_pool_message = bot.send_message(message.chat_id, pool['title'], reply_markup=render_keyboard( pool ))
    database.pool.update_one({"_id": pool['_id']}, {"$set": {"message_id": new_pool_message.message_id} })

def update_propose(pool, proposals, chat_id, bot, database):
    if [ p['propose'] for p in pool["proposals"] if p['propose'] in proposals] != proposals:
        for propose in proposals:
            if propose not in [ p['propose'] for p in pool["proposals"] ]:
                pool["proposals"].append({
                    "propose": propose, 
                    "voted_by": []
                })
        
        database.pool.update_one({"_id": pool['_id']}, {"$set": {'proposals': pool["proposals"]} })
        bot.edit_message_text(
            pool['title'], 
            chat_id=chat_id, 
            message_id=pool['message_id'], 
            reply_markup=render_keyboard( pool )
        )

def get_close_pool(_datetime, hour=0):
    close_datetime = datetime.datetime( _datetime.year, _datetime.month, _datetime.day, hour )
    return close_datetime

def day_to_add(_datetime, day, week_days):
    if _datetime.weekday() == 0:
        to_add = week_days.index(day)
    elif _datetime.weekday() == 6:
        to_add = week_days.index(day) + 1
    else:
        if week_days.index(day) <= _datetime.weekday():
            to_add = 5 + week_days.index(day)
        else:
            to_add = week_days.index(day) - _datetime.weekday()

    return to_add 
