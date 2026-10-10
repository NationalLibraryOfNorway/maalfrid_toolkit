import cchardet
from bs4 import UnicodeDammit
import logging
import os
import maalfrid_toolkit.config as c

# Create a logger for bs4 to capture warnings from UnicodeDammit
logger = logging.getLogger("bs4")
logger.setLevel(logging.WARNING)

# Capture warnings into a list
captured = []

class ListHandler(logging.Handler):
    def emit(self, record):
        captured.append(self.format(record))

logger.addHandler(ListHandler())

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

def detect_and_decode(data, is_html=False):
    """ This function tries to detect the encoding of a byte string and decode it"""
    if not data:
        return None

    # first try: strict utf-8
    # this is cheap, and very robust
    try:
        decoded = data.decode('utf-8-sig', errors='strict')
        return decoded, "utf-8"
    except UnicodeDecodeError:
        pass

    # second try: UnicodeDammit
    # passing is_htnl = True will intstruct UnicodeDammit to also consider
    # the declared encoding in the HTML header
    try:
        decoded = UnicodeDammit(data, is_html=is_html)
    except Exception:
        logger.warning("UnicodeDammit failed", exc_info=True)
        return None

    if decoded.unicode_markup is None:
        return None

    # fallback for Windows-1252
    if decoded.original_encoding in ("iso-8859-1", "latin-1", "latin1"):
        try:
            return data.decode("cp1252"), "windows-1252"
        except UnicodeDecodeError:
            pass

    return decoded.unicode_markup, decoded.original_encoding
