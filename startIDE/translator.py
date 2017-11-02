#!/usr/bin/python3

#
# provide localisation for index.py
#

import locale

# get system default locale
defaultlocale=locale.getdefaultlocale()[0]

# set default to English
LOCAL = "en"

# list of translations available, add new locales to this list
LANGLIST = ["en","de","fr"]

# determination of system preset, add new translations here, too
if "de_" in defaultlocale: LOCAL = "de"
elif "fr_" in defaultlocale: LOCAL = "fr"    

#
#
#
    
def getActiveLocale():
    # return the active localisation
    return LOCAL
    
def getLocalesList():
    # return list of translations available
    return LANGLIST

def translate(string, locale = LOCAL):
    #
    # translate the given string to the system default localisation or to a given localisation
    #
    #####################################
    # !!! Add new translations here !!! #
    #####################################
    
    if string == "This is a test":
        if local == "de": return "Dies ist ein Test"
        if local == "fr": return "C'est un test"    
        # if local == "another language": return "Translated text for this language"
    # if string == "another string":  
    #     if local == "de": return "Deutsche Übersetzung"
    #     if local == "fr": return "Traduction francaise"
    #     if local == "another language": return "Translated text for this language"
        
    
    # string not found or language not found:
    return string
    
