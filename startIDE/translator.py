#!/usr/bin/python3

import locale

defaultlocale=locale.getdefaultlocale()[0]

LOCAL = "en"

if "de_" in defaultlocale: LOCAL = "de"
elif "fr_" in defaultlocale: LOCAL = "fr"

print(defaultlocale, LOCAL)

def translate(string):
    if string == "This is a test":
        if LOCAL == "de": return "Dies ist ein Test"
        if LOCAL == "fr": return "C'est un test"

    
    
    # string not found or language not found:
    return string
    
