try:
    import fasttext
    from huggingface_hub import hf_hub_download
    fasttext_available = True
except ImportError:
    fasttext_available = False

import gielladetect as gd
import maalfrid_toolkit.config as c
from maalfrid_toolkit.utils import return_stoplists
import json
import sys
import os

# prefetch stoølists
stoplists = return_stoplists()

# placeholder for glotlid model
glotlid_model = None

# prefetch language filter
with open(os.path.join(c.LANGUAGE_FILTER_DIR, 'unique_stop_words_nob.txt'), 'r') as f:
    nob_filter = [x.strip() for x in f.readlines()]

with open(os.path.join(c.LANGUAGE_FILTER_DIR, 'unique_stop_words_nno.txt'), 'r') as f:
    nno_filter = [x.strip() for x in f.readlines()]

def get_glotlid_model():
    """ Function to load model into a global variable for faster fetching """
    global glotlid_model

    if glotlid_model is None:
        glotlid_model_path = hf_hub_download(repo_id="cis-lmu/glotlid", filename="model_v3.bin", cache_dir=None)
        glotlid_model = fasttext.load_model(glotlid_model_path)

    return glotlid_model

def get_stopword_density(stoplist, text):
    try:
        words = text.lower().strip().split()
        stopword_count = 0
        for word in words:
            if word in stoplist:
                stopword_count += 1

        word_count = len(words)
        if word_count == 0:
            stopword_density = 0
        else:
            stopword_density = 1.0 * stopword_count / word_count
    except:
        stopword_density = 0

    return stopword_density

def language_filter(text):
    try:
        words = text.lower().strip().split()
        nob_count = 0
        nno_count = 0
        for word in words:
            if word in nob_filter:
                nob_count += 1
            if word in nno_filter:
                nno_count += 1

        word_count = len(words)
        if word_count == 0:
            return None
        else:
            nob_density = 1.0 * nob_count / word_count
            nno_density = 1.0 * nno_count / word_count
    except:
        return None

    if nob_density > nno_density:
        return 'nob'
    elif nno_density > nob_density:
        return 'nno'
    else:
        return None

def run_fasttext(text, print_confidence=False, threshold=0.7):
    glotlid_model = get_glotlid_model()
    predictions = glotlid_model.predict(text)
    lang = str(predictions[0][0]).replace("__label__", "")
    lang = lang.split("_")[0]
    conf = round(predictions[1][0], 2)

    if print_confidence:
        lang = f"{lang} ({str(conf)})"
    else:
        lang = lang

    if threshold:
        if conf >= threshold:
            pass
        else:
            lang = ""

    return lang

def langdet(docId="", paras=[], stop_word_filter=True, apply_language_filter=True, engine="textcat"):
    documentStr = ' '.join(paras)

    # get doclang
    if engine == "glotlid" and fasttext_available == True:
        detect_language = run_fasttext
    elif engine == "glotlid" and fasttext_available == False:
        print("Fasttext not installed, only gielladetect is available.")
        detect_language = gd.detect
    else:
        detect_language = gd.detect

    lang = detect_language(documentStr)

    paralang = {}
    totaltokens = len(documentStr.split())
    number_of_paras = len(paras)

    for idx,line in enumerate(paras):
        tokens = len(line.split())
        linelang = ""

        if stop_word_filter == True:
            # loop through stoplists, look for stop word density for each set until threshold is met, otherwise do not classify
            for stoplist in c.stopword_filters:
                stop_density = get_stopword_density(stoplist=stoplists[stoplist], text=line)

                if stop_density >= c.STOPWORDS_LOW and tokens > 10:
                    # lowercase the line (and ensure no line breaks)
                    linelang = detect_language(line.lower().replace("\n", " "))
                    break
                else:
                    continue
        else:
            if tokens > 10:
                # lowercase the line (and ensure no line breaks)
                linelang = detect_language(line.lower().replace("\n", " "))

        # language filter for bokmål and nynorsk
        if apply_language_filter == True and linelang in ('nob', 'nno'):
            lang_filter_lang = language_filter(line)
            if lang_filter_lang:
                if linelang == lang_filter_lang:
                    pass
                else:
                    # if the opposite, use the language filter
                    linelang = lang_filter_lang
            else:
                # if inconclusive, use the model's answer
                pass

        # add to dict
        paralang[idx] = {"tokens": tokens, "lang": linelang}

    paralangstr = json.dumps(paralang)

    return (docId, lang, paralangstr, totaltokens, number_of_paras)

def run():
    with sys.stdin as f:
        paras = [line.strip() for line in f.readlines()]
        langStr = langdet(paras=paras, engine="textcat")
        for item in json.loads(langStr[2]).items():
            print(item)

if __name__ == '__main__':
    run()
