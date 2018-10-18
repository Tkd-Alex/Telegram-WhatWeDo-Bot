#!/usr/bin/python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup

def scrape_synonymous(word):
    req = requests.get("https://sapere.virgilio.it/parole/sinonimi-e-contrari/{}".format(word), timeout=5)
    soup = BeautifulSoup(req.text, 'html.parser')
    div = soup.find("div", {"class": "sct-descr"})
    return [ b.text for b in div.findAll('b') ]

def get_synonymous(database, word):
    synonymous = database.synonymous.find_one({"word": word})
    if synonymous is None:
            synonymous = scrape_synonymous(word)
            database.synonymous.insert_one({'word': word, 'synonymous': synonymous})
    else:
            synonymous = synonymous['synonymous']
    return synonymous
