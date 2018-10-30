#!/usr/bin/python3
# -*- coding: utf-8 -*-

# import requests, wikipediaapi, random, time
# from bs4 import BeautifulSoup

# proxies = open("proxies.txt","r").read().split("\n")
# headers = {'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36"}

import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

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

def render_keyboard(pool):
    keyboard = [ [] ]
    for index in range(0, len(pool["proposals"])):
        if len(keyboard[len(keyboard)-1]) == 3:
            keyboard.append([])

        callback_data = json.dumps({ 'index': index, 'pool_id': str(pool['_id']) })
        keyboard[len(keyboard)-1].append(
            InlineKeyboardButton( 
                "{} {}".format(
                    pool["proposals"][index]["propose"].capitalize(), 
                    "" if len(pool["proposals"][index]["voted_by"]) == 0 else "({})".format(len(pool["proposals"][index]["voted_by"])) 
            ) , callback_data=callback_data ) 
        )

    return InlineKeyboardMarkup(keyboard)

"""
def scrape_synonymous(word):
    try:
        random.seed(time.perf_counter())
        proxy = random.choice(proxies)
        proxy = { 'http': 'http://{}'.format(proxy), 'https': 'http://{}'.format(proxy)}
        req = requests.get("https://sapere.virgilio.it/parole/sinonimi-e-contrari/{}".format(word), timeout=5, proxies=proxy, headers=headers)
        soup = BeautifulSoup(req.text, 'html.parser')
        div = soup.find("div", {"class": "sct-descr"})
        return [ b.text for b in div.findAll('b') ] if div != None else []
    except Exception as e:
        print("There was an error with synonymous: {}".format(e))
        return []
        
def get_synonymous(database, word):
    synonymous = database.synonymous.find_one({"word": word})
    if synonymous is None:
        synonymous = scrape_synonymous(word)
        database.synonymous.insert_one({'word': word, 'synonymous': synonymous})
    else:
        synonymous = synonymous['synonymous']
        return synonymous
"""
