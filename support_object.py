day_transformers = {
    "domani": 1,
    "dopodomani": 2
}

time_pointers = {
    "stasera": 20,
    "sera": 20,
    "pranzo": 13,
    "cena": 21,
    "colazione": 8,
    "oggi": 0
}

prepositions = {
    "di":       False, # a casa di alex (?)
    "del":      False,
    "dello":    False,
    "della":    False,
    "dei":      False,
    "degli":    False,
    "delle":    False,
    
    "a":        True, # a piedi? (solved with dict)
    "al":       True,
    "allo":     True,
    "alla":     True,
    "ai":       False,
    "agli":     False,
    "alle":     False,

    "da":       False,
    "dal":      False,
    "dallo":    False,
    "dalla":    False,
    "dai":      False,
    "dagli":    False,
    "dalle":    False,

    "in":       True, # in auto? (solved with dict)
    "nel":      False,
    "nello":    False,
    "nella":    False,
    "nei":      False,
    "negli":    False,
    "nelle":    False,

    "con":      False,

    "su":       False,
    "sul":      False,
    "sullo":    False,
    "sulla":    False,
    "sui":      False,
    "sugli":    False,
    "sulle":    False,

    "per":      False,

    "tra":      False,

    "fra":      False
}