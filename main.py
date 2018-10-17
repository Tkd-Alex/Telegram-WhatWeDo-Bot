#!/usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import treetaggerwrapper, re, nltk
from pprint import pprint

# nltk.download('punkt')

# treetaggerwrapper.enable_debugging_log()
tagger = treetaggerwrapper.TreeTagger(TAGLANG='it', TAGDIR='./TreeTagger', TAGPARFILE='./TreeTagger/lib/italian.par')
message = 'Non ho vogl.ia di fare niente sta sera. anche se pensavo di andare al cinema. Che ne dite?'
sentences = nltk.sent_tokenize( message )
for sentence in sentences:
    tags_encoded = tagger.tag_text( sentence )
    tags = treetaggerwrapper.make_tags( tags_encoded )

    pprint(tags)

    propose = [ 'andare', 'fare' ]
    negation = [ 'non' ]

    is_negate = False
    for tag in tags:
        if tag.word in negation:
            is_negate = True

        if tag.pos.startswith("VER") and tag.lemma in propose and is_negate is False :
            print("C'è l'intenzione di voler fare qualcosa")
