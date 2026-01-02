import pytest
import maalfrid_toolkit.utils as utils

def test_get_stoplist():
    stoplist = utils.get_stoplist("Norwegian_NRK")
    assert isinstance(stoplist, set)

def test_return_all_stop_words():
    stopwords = utils.return_all_stop_words()
    assert isinstance(stopwords, set)

def test_return_stoplists():
    stoplists = utils.return_stoplists()
    assert isinstance(stoplists, dict)

def test_detect_and_decode(old_encoding, new_encoding, invalid_start_byte):
    assert utils.detect_and_decode(old_encoding) == 'Æøå må stemme her!'
    assert utils.detect_and_decode(new_encoding) == 'Æøå må stemme her!'
    assert utils.detect_and_decode(invalid_start_byte) == 'Søk'
