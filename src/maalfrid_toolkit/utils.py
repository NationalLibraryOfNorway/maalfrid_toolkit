import cchardet
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

# INSPIRED BY: https://github.com/bitextor/bitextor/blob/master/bitextor-warc2htmlwarc.py and JUSTEXT
def detect_and_decode(data):
    """ This function takes a binary string and tries to guess its encoding, returning a decoded utf8 string """
    if len(data) > 0:
        # first try: strict utf-8
        try:
            decoded = data.decode('utf-8', errors='strict')
            return decoded
        except:
            pass

        # guess encoding, try fallback encodings
        try_encs = ['iso-8859-1', 'windows‑1252']
        try:
            encoding = cchardet.detect(data)['encoding']
            try_encs.insert(0, encoding)
        except:
            pass

        for enc in try_encs:
            try:
                decoded = data.decode(enc)
                return decoded
            except:
                pass

        # last fallback: utf-8 with replacements
        try:
            decoded = data.decode('utf-8', errors='replace')
            return decoded
        except:
            pass

    return None