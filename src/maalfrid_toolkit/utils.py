import cchardet
from bs4 import UnicodeDammit
import os
import maalfrid_toolkit.config as c

# Helper functions adapted from the Justext package for loading stoplists outside of the Justext package
def get_stoplists():
    "Returns a list of inbuilt stoplists."
    stoplists = []
    stoplists_dir = c.JUSTEXT_STOPLISTS_DIR
    for filename in os.listdir(stoplists_dir):
        if filename.endswith('.txt'):
            stoplists.append(filename.rsplit('.', 1)[0])
    return stoplists

def get_stoplist(language):
    "Returns an inbuilt stoplist for the language as a set of words."
    with open(os.path.join(c.JUSTEXT_STOPLISTS_DIR, language + ".txt"), 'rb') as f:
        stoplist_contents = f.read().decode("utf-8")
        return set(l.strip().lower() for l in stoplist_contents.split(u'\n'))

def return_all_stop_words():
    """ Return all stoplists in one list """
    stop_words = set()
    for language in get_stoplists():
        stop_words.update(get_stoplist(language))
    return stop_words

def return_stoplists():
    """ Return stoplists in dictionary, one per language model """
    stoplist_langs = get_stoplists()
    stoplists = {}
    for stoplist_lang in stoplist_langs:
        stoplists[stoplist_lang] = get_stoplist(stoplist_lang)
    return stoplists

def detect_and_decode(data):
    """ This function uses BeautifulSoup's UnicodeDammit to decode an HTML string"""
    if len(data) > 0:
        try:
            html = UnicodeDammit(data)
            return html.unicode_markup
        except:
            return None
    return None