#!/usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import treetaggerwrapper, re, nltk, utils
from pprint import pprint
from pymongo import MongoClient

nltk.download('punkt')

client = MongoClient()
database = client[ 'word_history' ]

proposes = [ 'andare', 'fare' ]
proposes += utils.get_synonymous(database, 'andare')
proposes += utils.get_synonymous(database, 'fare')

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

negation = [ 'non' ]

tagger = treetaggerwrapper.TreeTagger(TAGLANG='it', TAGDIR='./TreeTagger', TAGPARFILE='./TreeTagger/lib/italian.par')
message = 'Andiamo stasera in qualche posto? Bingo?'
sentences = nltk.sent_tokenize( message.lower() )

for sentence in sentences:
        tags_encoded = tagger.tag_text( sentence )
        tags = treetaggerwrapper.make_tags( tags_encoded )

        is_negate = False
        preposition_before = False
        for tag in tags:

                synonymous = None
                if tag.pos.startswith(("VER", "PRO", "NPR", "NOM", "ADJ")):
                        synonymous = utils.get_synonymous(database, tag.word)

                if tag.word in negation:
                        is_negate = True

                if tag.pos.startswith(("VER", "NOM")) and preposition_before is True:
                        print("Il luogo o l'azione che si vuole compiere è", tag)

                if tag.pos.startswith("VER") and tag.lemma in proposes and is_negate is False:
                        print(sentence, "C'è l'intenzione di voler fare qualcosa", tag)

                # Foundend preposition maybe the next word is a 'place' or 'action to do'
                # Anzichè escludere DI conviene includere solo A
                preposition_before = True if tag.pos.startswith("PRE") and tag.word != 'di' and not tag.word in preposition['di'] else False
                        
                        