import pytest
from bs4 import BeautifulSoup
from maalfrid_toolkit.utils import convert_encoding, return_all_stop_words
import maalfrid_toolkit.htmlclean as htmlclean

@pytest.fixture
def broken_html():
    """ This example contains broken HTML (unclosed tags) """
    return "<html><head><title>Test</title></head><body><h1>Hello World"

@pytest.fixture
def links_in_html():
    """ This example contains absolute and relative links in valid HTML """
    return "<html><body><div>Here is <a href='https://www.nb.no/search'>a</a> link. There is <a href='/sprakbanken'>another one</a>.</div></body></html>"

@pytest.fixture
def html_with_boilerplate():
    """ This example contains a valid HTML document with article-like text in Norwegian Nynorsk among boilerplate """
    return """<!DOCTYPE html><html lang="nn"><head><meta charset="UTF-8"><title>Nasjonalbiblioteket: Språkbankens ressurskatalog</title></head><body><header><h1>Nasjonalbiblioteket: Språkbankens ressurskatalog</h1><nav><ul><li><a href="#">Språkbanken</a></li><li><a href="#">Nyhende</a></li><li><a href="#">Ressurskatalogen</a></li><li><a href="#">Om Språkbanken</a></li></ul></nav></header><aside><h3>Ressurskatalogen</h3><ul><li><a href="#">CLARINO</a></li><li><a href="#">Felles datakatalog</a></li></ul></aside><main><article><h2>Målfrid 2024 – Fritt tilgjengelege tekster frå norske statlege nettsider</h2><p>Dette korpuset inneheld dokument frå 497 internettdomene tilknytta norske statlege institusjonar. Totalt består materialet av omlag 2,6 milliardar «tokens» (ord og teiknsetting). I tillegg til tekster på bokmål og nynorsk inneheld korpuset tekster på nordsamisk, lulesamisk, sørsamisk og engelsk.</p><p>Dataa vart samla inn som ein lekk i Målfrid-prosjektet, der Nasjonalbiblioteket på vegner av Kulturdepartementet og i samarbeid med Språkrådet haustar og aggregerer tekstdata for å dokumentere bruken av bokmål og nynorsk hjå statlege institusjonar.</p><p>Språkbanken føretok ei fokusert hausting av nettsidene til dei aktuelle institusjonane mellom desember 2023 og januar 2024. Tekstdokument (HTML, DOC(X)/ODT og PDF) vart lasta ned rekursivt frå dei ulike domena, 12 nivå ned på nettsidene. Me tok ålmenne høflegheitsomsyn og respekterte robots.txt.</p></article></main><footer><p>Organisasjonsnummer 976 029 100</p></footer></body></html>"""

def test_get_lxml_tree(broken_html):
    parsed_html = htmlclean.get_lxml_tree(broken_html, use_lenient_html_parser=False)

    # ensure function got the h1 element right
    assert parsed_html.xpath('//h1')[0].text == "Hello World"

def test_get_links(links_in_html):
    parsed_html = htmlclean.get_lxml_tree(links_in_html, use_lenient_html_parser=False)
    links = htmlclean.get_links(parsed_html, "https://www.nb.no")
    correct_links = [('https://www.nb.no/search', 'a'), ('https://www.nb.no/sprakbanken', 'another one')]
    assert links == correct_links

def test_remove_bp(html_with_boilerplate):
    stop_words = return_all_stop_words()
    parsed_html = htmlclean.get_lxml_tree(html_with_boilerplate, use_lenient_html_parser=False)
    paragraphs = htmlclean.removeBP(parsed_html, stop_words)
    assert len(paragraphs) == 5
