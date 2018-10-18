#!/usr/bin/python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup

def scrape_synonymous(word):
    req = requests.get("https://sapere.virgilio.it/parole/sinonimi-e-contrari/{}".format(word), timeout=5)
    soup = BeautifulSoup(req.text, 'html.parser')
    div = soup.find("div", {"class": "sct-descr"})
    return [ b.text for b in div.findAll('b') ]