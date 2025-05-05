import pytest
import maalfrid_toolkit.langdet as langdet
from maalfrid_toolkit.utils import get_stoplist

@pytest.fixture
def text_unclear():
	return 'Dette er ei setning på bokmål/nynorsk.'

@pytest.fixture
def text_nno():
	return 'Dette er ikkje ei setning på bokmål.'

@pytest.fixture
def text_nob():
	return 'Dette er ikke en setning på nynorsk.'

@pytest.fixture
def longer_text_nno():
	return 'Dette korpuset inneheld dokument frå 497 internettdomene tilknytta norske statlege institusjonar. Totalt består materialet av omlag 2,6 milliardar «tokens» (ord og teiknsetting). I tillegg til tekster på bokmål og nynorsk inneheld korpuset tekster på nordsamisk, lulesamisk, sørsamisk og engelsk.'

def test_get_stopword_density(text_unclear, text_nno, text_nob):
	assert langdet.get_stopword_density(get_stoplist("Norwegian_NRK"), text_nno) > 0.7

def test_language_filter(text_unclear, text_nno, text_nob):
	assert langdet.language_filter(text_unclear) == None
	assert langdet.language_filter(text_nob) == "nob"
	assert langdet.language_filter(text_nno) == "nno"

def test_langdet(longer_text_nno):
	lang_textcat = langdet.langdet(docId="testdoc", paras=[longer_text_nno], stop_word_filter=False, apply_language_filter=False, engine="textcat")
	lang_glotlid = langdet.langdet(docId="testdoc", paras=[longer_text_nno], stop_word_filter=False, apply_language_filter=False, engine="glotlid")
	assert lang_textcat[1] == 'nno'
	assert lang_glotlid[1] == 'nno'
