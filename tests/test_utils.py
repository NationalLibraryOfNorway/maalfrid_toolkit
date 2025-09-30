import pytest
import maalfrid_toolkit.utils as utils

@pytest.fixture
def new_encoding():
    # encode a string as UTF-8 (standard)
    return 'Æøå må stemme her!'.encode("utf-8")

@pytest.fixture
def old_encoding():
    # encode a string as CP1252 (ANSI style - 1990s, early 2000s)
    return 'Æøå må stemme her!'.encode("cp1252")

def test_get_stoplist():
    stoplist = utils.get_stoplist("Norwegian_NRK")
    assert isinstance(stoplist, set)

def test_return_all_stop_words():
    stopwords = utils.return_all_stop_words()
    assert isinstance(stopwords, set)

def test_return_stoplists():
    stoplists = utils.return_stoplists()
    assert isinstance(stoplists, dict)

def test_detect_and_decode(old_encoding, new_encoding):
    assert utils.detect_and_decode(old_encoding) == 'Æøå må stemme her!'
    assert utils.detect_and_decode(new_encoding) == 'Æøå må stemme her!'
