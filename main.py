#!/usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import treetaggerwrapper, re, nltk, italian_dictionary, utils
from pprint import pprint
from pymongo import MongoClient

nltk.download('punkt')

client = MongoClient()
database = client[ 'word_history' ]

propose = [ 'andare', 'fare' ]
negation = [ 'non' ]

tagger = treetaggerwrapper.TreeTagger(TAGLANG='it', TAGDIR='./TreeTagger', TAGPARFILE='./TreeTagger/lib/italian.par')
message = 'Non ho vogl. ia di fare niente sta sera. anche se pensavo di andare al cinema. Che ne dite?'
sentences = nltk.sent_tokenize( message )

for sentence in sentences:
    print("Sentence: {}".format(sentence))

    tags_encoded = tagger.tag_text( sentence )
    tags = treetaggerwrapper.make_tags( tags_encoded )

    is_negate = False
    for tag in tags:
        print(tag)

        if tag.pos.startswith(("VER", "PRO", "NPR", "NOM", "ADJ")):
                synonymous = database.synonymous.find_one({"word": tag.word})
                if synonymous is None:
                        synonymous = utils.scrape_synonymous(tag.word)
                        database.synonymous.insert_one({'word': tag.word, 'synonymous': synonymous})
                else:
                        synonymous = synonymous['synonymous']

                print(synonymous)
                print("==============")

        # if tag.word in negation:
        #     is_negate = True

        # if tag.pos.startswith("VER") and tag.lemma in propose and is_negate is False :
        #     print("C'è l'intenzione di voler fare qualcosa")