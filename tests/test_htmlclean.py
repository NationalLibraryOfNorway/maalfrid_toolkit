import pytest
from maalfrid_toolkit.utils import return_all_stop_words
import maalfrid_toolkit.htmlclean as htmlclean

@pytest.fixture
def broken_html():
    """ This example contains broken HTML (unclosed tags) """
    return "<html><head><title>Test</title></head><body><h1>Hello World".encode("utf-8")

@pytest.fixture
def html_wrong_encoding_declaration():
    return """<!DOCTYPE html><html lang="nn"><head><meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"><title>Nasjonalbiblioteket: Språkbankens ressurskatalog</title></head><body><header><h1>Nasjonalbiblioteket: Språkbankens ressurskatalog</h1><nav><ul><li><a href="#">Språkbanken</a></li><li><a href="#">Nyhende</a></li><li><a href="#">Ressurskatalogen</a></li><li><a href="#">Om Språkbanken</a></li></ul></nav></header><aside><h3>Ressurskatalogen</h3><ul><li><a href="#">CLARINO</a></li><li><a href="#">Felles datakatalog</a></li></ul></aside><main><article><h2>Målfrid 2024 – Fritt tilgjengelege tekster frå norske statlege nettsider</h2><p>Dette korpuset inneheld dokument frå 497 internettdomene tilknytta norske statlege institusjonar. Totalt består materialet av omlag 2,6 milliardar «tokens» (ord og teiknsetting). I tillegg til tekster på bokmål og nynorsk inneheld korpuset tekster på nordsamisk, lulesamisk, sørsamisk og engelsk.</p><p>Dataa vart samla inn som ein lekk i Målfrid-prosjektet, der Nasjonalbiblioteket på vegner av Kulturdepartementet og i samarbeid med Språkrådet haustar og aggregerer tekstdata for å dokumentere bruken av bokmål og nynorsk hjå statlege institusjonar.</p><p>Språkbanken føretok ei fokusert hausting av nettsidene til dei aktuelle institusjonane mellom desember 2023 og januar 2024. Tekstdokument (HTML, DOC(X)/ODT og PDF) vart lasta ned rekursivt frå dei ulike domena, 12 nivå ned på nettsidene. Me tok ålmenne høflegheitsomsyn og respekterte robots.txt.</p></article></main><footer><p>Organisasjonsnummer 976 029 100</p></footer></body></html>""".encode("utf-8")

@pytest.fixture
def xhtml_unicode_string_with_encoding_declaration():
    return """<?xml version="1.0" encoding="ISO-8859-1"?><!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"><html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en"><head><title>Eksempel-XHTML fra Nasjonalbiblioteket</title><meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1" /><meta property="og:site_name" content="Nasjonalbiblioteket" /</head><body><p>Hello, world! — med ISO‑8859‑1-kodering.</p></body></html>""".encode("utf-8")

@pytest.fixture
def links_in_html():
    """ This example contains absolute and relative links in valid HTML """
    return "<html><body><div>Here is <a href='https://www.nb.no/search'>a</a> link. There is <a href='/sprakbanken'>another one</a>.</div></body></html>".encode("utf-8")

@pytest.fixture
def html_with_boilerplate():
    """ This example contains a valid HTML document with article-like text in Norwegian Nynorsk among boilerplate """
    return """<!DOCTYPE html><html lang="nn"><head><meta charset="UTF-8"><meta property="og:site_name" content="Nasjonalbiblioteket"><meta property="article:modified_time" content="2025-09-30T09:14:25+00:00"><title>Nasjonalbiblioteket: Språkbankens ressurskatalog</title></head><body><header><h1>Nasjonalbiblioteket: Språkbankens ressurskatalog</h1><nav><ul><li><a href="#">Språkbanken</a></li><li><a href="#">Nyhende</a></li><li><a href="#">Ressurskatalogen</a></li><li><a href="#">Om Språkbanken</a></li></ul></nav></header><aside><h3>Ressurskatalogen</h3><ul><li><a href="#">CLARINO</a></li><li><a href="#">Felles datakatalog</a></li></ul></aside><main><article><h2>Målfrid 2024 – Fritt tilgjengelege tekster frå norske statlege nettsider</h2><p>Dette korpuset inneheld dokument frå 497 internettdomene tilknytta norske statlege institusjonar. Totalt består materialet av omlag 2,6 milliardar «tokens» (ord og teiknsetting). I tillegg til tekster på bokmål og nynorsk inneheld korpuset tekster på nordsamisk, lulesamisk, sørsamisk og engelsk.</p><p>Dataa vart samla inn som ein lekk i Målfrid-prosjektet, der Nasjonalbiblioteket på vegner av Kulturdepartementet og i samarbeid med Språkrådet haustar og aggregerer tekstdata for å dokumentere bruken av bokmål og nynorsk hjå statlege institusjonar.</p><p>Språkbanken føretok ei fokusert hausting av nettsidene til dei aktuelle institusjonane mellom desember 2023 og januar 2024. Tekstdokument (HTML, DOC(X)/ODT og PDF) vart lasta ned rekursivt frå dei ulike domena, 12 nivå ned på nettsidene. Me tok ålmenne høflegheitsomsyn og respekterte robots.txt.</p></article></main><footer><p>Organisasjonsnummer 976 029 100</p></footer></body></html>""".encode("utf-8")

def test_get_lxml_tree(broken_html):
    parsed_html = htmlclean.get_lxml_tree(broken_html, use_lenient_html_parser=False)

    # ensure function got the h1 element right
    assert parsed_html.xpath('//h1')[0].text == "Hello World"

def test_get_lxml_tree_wrong_decoding_declaration(html_wrong_encoding_declaration):
    parsed_html = htmlclean.get_lxml_tree(html_wrong_encoding_declaration, use_lenient_html_parser=False)

    # ensure LXML.html.fromstring does not try to use the faulty encoding declaration
    assert parsed_html.text_content() == 'Nasjonalbiblioteket: Språkbankens ressurskatalogNasjonalbiblioteket: Språkbankens ressurskatalogSpråkbankenNyhendeRessurskatalogenOm SpråkbankenRessurskatalogenCLARINOFelles datakatalogMålfrid 2024 – Fritt tilgjengelege tekster frå norske statlege nettsiderDette korpuset inneheld dokument frå 497 internettdomene tilknytta norske statlege institusjonar. Totalt består materialet av omlag 2,6 milliardar «tokens» (ord og teiknsetting). I tillegg til tekster på bokmål og nynorsk inneheld korpuset tekster på nordsamisk, lulesamisk, sørsamisk og engelsk.Dataa vart samla inn som ein lekk i Målfrid-prosjektet, der Nasjonalbiblioteket på vegner av Kulturdepartementet og i samarbeid med Språkrådet haustar og aggregerer tekstdata for å dokumentere bruken av bokmål og nynorsk hjå statlege institusjonar.Språkbanken føretok ei fokusert hausting av nettsidene til dei aktuelle institusjonane mellom desember 2023 og januar 2024. Tekstdokument (HTML, DOC(X)/ODT og PDF) vart lasta ned rekursivt frå dei ulike domena, 12 nivå ned på nettsidene. Me tok ålmenne høflegheitsomsyn og respekterte robots.txt.Organisasjonsnummer 976 029 100'

def test_get_lxml_tree_wrong_decoding_declaration_lenient(html_wrong_encoding_declaration):
    parsed_html = htmlclean.get_lxml_tree(html_wrong_encoding_declaration, use_lenient_html_parser=True)

    # ensure LXML.html.fromstring does not try to use the faulty encoding declaration
    assert parsed_html.text_content() == 'Nasjonalbiblioteket: Språkbankens ressurskatalogNasjonalbiblioteket: Språkbankens ressurskatalogSpråkbankenNyhendeRessurskatalogenOm SpråkbankenRessurskatalogenCLARINOFelles datakatalogMålfrid 2024 – Fritt tilgjengelege tekster frå norske statlege nettsiderDette korpuset inneheld dokument frå 497 internettdomene tilknytta norske statlege institusjonar. Totalt består materialet av omlag 2,6 milliardar «tokens» (ord og teiknsetting). I tillegg til tekster på bokmål og nynorsk inneheld korpuset tekster på nordsamisk, lulesamisk, sørsamisk og engelsk.Dataa vart samla inn som ein lekk i Målfrid-prosjektet, der Nasjonalbiblioteket på vegner av Kulturdepartementet og i samarbeid med Språkrådet haustar og aggregerer tekstdata for å dokumentere bruken av bokmål og nynorsk hjå statlege institusjonar.Språkbanken føretok ei fokusert hausting av nettsidene til dei aktuelle institusjonane mellom desember 2023 og januar 2024. Tekstdokument (HTML, DOC(X)/ODT og PDF) vart lasta ned rekursivt frå dei ulike domena, 12 nivå ned på nettsidene. Me tok ålmenne høflegheitsomsyn og respekterte robots.txt.Organisasjonsnummer 976 029 100'

def test_get_lxml_tree_with_xhtml_encoding_declaration(xhtml_unicode_string_with_encoding_declaration):
    parsed_html = htmlclean.get_lxml_tree(xhtml_unicode_string_with_encoding_declaration, use_lenient_html_parser=False)

def test_get_lxml_tree_with_xhtml_encoding_declaration_lenient(xhtml_unicode_string_with_encoding_declaration):
    parsed_html = htmlclean.get_lxml_tree(xhtml_unicode_string_with_encoding_declaration, use_lenient_html_parser=True)

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

def test_get_title(html_with_boilerplate, xhtml_unicode_string_with_encoding_declaration):
    # Case 1: document has a title
    tree = htmlclean.get_lxml_tree(html_with_boilerplate)
    title = htmlclean.get_title(tree)
    assert title == "Nasjonalbiblioteket: Språkbankens ressurskatalog"

    # Case 2: document has no title
    for head_title in tree.xpath('//head/title'):
        head_title.getparent().remove(head_title)

    title = htmlclean.get_title(tree)

    assert title == None

    # Case 3: tree is None
    tree = None
    title = htmlclean.get_title(tree)

    assert title == None

    # Case 4: test XHTML
    tree = htmlclean.get_lxml_tree(xhtml_unicode_string_with_encoding_declaration)
    title = htmlclean.get_title(tree)

    assert title == "Eksempel-XHTML fra Nasjonalbiblioteket"

def test_get_metadata(html_with_boilerplate, xhtml_unicode_string_with_encoding_declaration):
    # Case 1: document has a title
    tree = htmlclean.get_lxml_tree(html_with_boilerplate)
    metadata = htmlclean.get_metadata(tree)
    assert metadata == {'article:modified_time': '2025-09-30T09:14:25+00:00', 'og:site_name': 'Nasjonalbiblioteket'}

    # Case 2: document has no metadata
    for head_meta in tree.xpath('//head/meta'):
        head_meta.getparent().remove(head_meta)

    metadata = htmlclean.get_metadata(tree)

    assert metadata == None

    # Case 3: tree is None
    tree = None
    metadata = htmlclean.get_metadata(tree)

    assert metadata == None

    # Case 4: test XHTML
    tree = htmlclean.get_lxml_tree(xhtml_unicode_string_with_encoding_declaration)
    metadata = htmlclean.get_metadata(tree)

    assert metadata == {'og:site_name': 'Nasjonalbiblioteket'}

