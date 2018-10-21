#!/usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import treetaggerwrapper, re, nltk, utils, wikipediaapi, time, random, threading
from joblib import Parallel, delayed
from datetime import datetime
from pprint import pprint
from pymongo import MongoClient

client = MongoClient()
database = client[ 'word_analysis' ]

tagger = treetaggerwrapper.TreeTagger(TAGLANG='it', TAGDIR='./TreeTagger', TAGPARFILE='./TreeTagger/lib/italian.par')

proxies = open("proxies.txt","r").read().split("\n")
wiki_wiki = wikipediaapi.Wikipedia('it', proxies=proxies)

def return_pos(word):
    tags_encoded = tagger.tag_text( word )
    tags = treetaggerwrapper.make_tags( tags_encoded )
    return tags[0].pos if len(tags) != 0 else ""

def update_word(word, index, total):
    try:
        if database.words.find_one({'word': word}) is None:
            random.seed(time.perf_counter())
            time.sleep(random.randint(0, 3))
            page_py = wiki_wiki.page(word)
            database.words.insert_one({'word': word, 'synonymous': utils.scrape_synonymous(word), 'summary': page_py.summary})   
            print("[{}/{}] COMPLETE".format(index, total), datetime.now().strftime('%Y/%m/%d %H:%M:%S'), word)
        else:
           print("[{}/{}] ALREADY IN DB".format(index, total), datetime.now().strftime('%Y/%m/%d %H:%M:%S'), word)
    except Exception as e:
        print("There was an error during update_word: {}".format(e))

dictionary = []
dictionary += [ p.rstrip() for p in open("paroleitaliane/1000_parole_italiane_comuni.txt","r").readlines() ]
dictionary += [ p.rstrip() for p in open("paroleitaliane/110000_parole_italiane_con_nomi_propri.txt","r").readlines() ]
dictionary += [ p.rstrip() for p in open("paroleitaliane/280000_parole_italiane.txt","r").readlines() ]
dictionary += [ p.rstrip() for p in open("paroleitaliane/400_parole_composte.txt","r").readlines() ]
dictionary += [ p.rstrip() for p in open("paroleitaliane/60000_parole_italiane.txt","r").readlines() ]
dictionary += [ p.rstrip() for p in open("paroleitaliane/660000_parole_italiane.txt","r").readlines() ]
dictionary += [ p.rstrip() for p in open("paroleitaliane/95000_parole_italiane_con_nomi_propri.txt","r").readlines() ]
dictionary += [ p.rstrip() for p in open("paroleitaliane/parole_uniche.txt","r").readlines() ]

# dictionary += [ p.rstrip() for p in open("lista_badwords.txt","r").readlines() ]
# dictionary += [ p.rstrip() for p in open("lista_cognomi.txt","r").readlines() ]
# dictionary += [ p.rstrip() for p in open("9000_nomi_propri.txt","r").readlines() ]

print("Total word collect: {}".format(len(dictionary)))
dictionary = list(set(dictionary))
print("Word without duplicate: {}".format(len(dictionary)))
dictionary = [ d.lower() for d in dictionary if return_pos(d).startswith(("NPR", "NOM")) ]
print("Only NOM noun and NPR name: {}".format(len(dictionary)))

Parallel(n_jobs=150, backend="threading")( delayed(update_word)(dictionary[index], index, len(dictionary)) for index in range(0, len(dictionary)) )