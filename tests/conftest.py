import pytest

@pytest.fixture
def new_encoding():
    """ Encode a string as UTF-8 (standard) """
    return 'Æøå må stemme her!'.encode("utf-8")

@pytest.fixture
def old_encoding():
    """ Encode a string as CP1252 (ANSI style - 1990s, early 2000s) """
    return 'Æøå må stemme her!'.encode("cp1252")

@pytest.fixture()
def invalid_start_byte():
    """ Return a byte string with invalid utf-8 start byte """
    return b'S\xf8k'

@pytest.fixture
def broken_html():
    """ Broken HTML (unclosed tags) """
    return "<html><head><title>Test</title></head><body><h1>Hello World".encode("utf-8")

@pytest.fixture
def html_wrong_encoding_declaration():
    """ A UTF-8 byte string with HTML and wrong encoding declaration """
    return """<!DOCTYPE html><html lang="nn"><head><meta http-equiv="Content-Type" charset="iso-8859-1" content="text/html; charset=iso-8859-1"><title>Nasjonalbiblioteket: Språkbankens ressurskatalog</title></head><body><header><h1>Nasjonalbiblioteket: Språkbankens ressurskatalog</h1><nav><ul><li><a href="#">Språkbanken</a></li><li><a href="#">Nyhende</a></li><li><a href="#">Ressurskatalogen</a></li><li><a href="#">Om Språkbanken</a></li></ul></nav></header><aside><h3>Ressurskatalogen</h3><ul><li><a href="#">CLARINO</a></li><li><a href="#">Felles datakatalog</a></li></ul></aside><main><article><h2>Målfrid 2024 – Fritt tilgjengelege tekster frå norske statlege nettsider</h2><p>Dette korpuset inneheld dokument frå 497 internettdomene tilknytta norske statlege institusjonar. Totalt består materialet av omlag 2,6 milliardar «tokens» (ord og teiknsetting). I tillegg til tekster på bokmål og nynorsk inneheld korpuset tekster på nordsamisk, lulesamisk, sørsamisk og engelsk.</p><p>Dataa vart samla inn som ein lekk i Målfrid-prosjektet, der Nasjonalbiblioteket på vegner av Kulturdepartementet og i samarbeid med Språkrådet haustar og aggregerer tekstdata for å dokumentere bruken av bokmål og nynorsk hjå statlege institusjonar.</p><p>Språkbanken føretok ei fokusert hausting av nettsidene til dei aktuelle institusjonane mellom desember 2023 og januar 2024. Tekstdokument (HTML, DOC(X)/ODT og PDF) vart lasta ned rekursivt frå dei ulike domena, 12 nivå ned på nettsidene. Me tok ålmenne høflegheitsomsyn og respekterte robots.txt.</p></article></main><footer><p>Organisasjonsnummer 976 029 100</p></footer></body></html>""".encode("utf-8")

@pytest.fixture
def html_wrong_encoding_declaration_text_content():
    """ The text content of html_wrong_encoding_declaration """
    return 'Nasjonalbiblioteket: Språkbankens ressurskatalogNasjonalbiblioteket: Språkbankens ressurskatalogSpråkbankenNyhendeRessurskatalogenOm SpråkbankenRessurskatalogenCLARINOFelles datakatalogMålfrid 2024 – Fritt tilgjengelege tekster frå norske statlege nettsiderDette korpuset inneheld dokument frå 497 internettdomene tilknytta norske statlege institusjonar. Totalt består materialet av omlag 2,6 milliardar «tokens» (ord og teiknsetting). I tillegg til tekster på bokmål og nynorsk inneheld korpuset tekster på nordsamisk, lulesamisk, sørsamisk og engelsk.Dataa vart samla inn som ein lekk i Målfrid-prosjektet, der Nasjonalbiblioteket på vegner av Kulturdepartementet og i samarbeid med Språkrådet haustar og aggregerer tekstdata for å dokumentere bruken av bokmål og nynorsk hjå statlege institusjonar.Språkbanken føretok ei fokusert hausting av nettsidene til dei aktuelle institusjonane mellom desember 2023 og januar 2024. Tekstdokument (HTML, DOC(X)/ODT og PDF) vart lasta ned rekursivt frå dei ulike domena, 12 nivå ned på nettsidene. Me tok ålmenne høflegheitsomsyn og respekterte robots.txt.Organisasjonsnummer 976 029 100'

@pytest.fixture
def html_encoding_declaration_invalid_bytestring():
    """ A byte string containing invalid start byte """
    return b'<!DOCTYPE html><html lang="nn"><head><meta http-equiv="Content-Type" charset="UTF-8" content="text/html; charset=UTF-8"><title>Nasjonalbiblioteket: Spr\xc3\xa5kbankens ressurskatalog</title></head><body><header><h1>Nasjonalbiblioteket: Spr\xc3\xa5kbankens ressurskatalog</h1><nav><ul><li><a href="#">Spr\xc3\xa5kbanken</a></li><li><a href="#">Nyhende</a></li><li><a href="#">Ressurskatalogen</a></li><li><a href="#">Om Spr\xc3\xa5kbanken</a></li></ul></nav></header><aside><h3>Ressurskatalogen</h3><ul><li><a href="#">CLARINO</a></li><li><a href="#">Felles datakatalog</a></li></ul></aside><main><article><h2>M\xf8frid 2024 \xe2\x80\x93 Fritt tilgjengelege tekster fr\xc3\xa5 norske statlege nettsider</h2><p>Dette korpuset inneheld dokument fr\xc3\xa5 497 internettdomene tilknytta norske statlege institusjonar. Totalt best\xc3\xa5r materialet av omlag 2,6 milliardar \xc2\xabtokens\xc2\xbb (ord og teiknsetting). I tillegg til tekster p\xc3\xa5 bokm\xc3\xa5l og nynorsk inneheld korpuset tekster p\xc3\xa5 nordsamisk, lulesamisk, s\xc3\xb8rsamisk og engelsk.</p><p>Dataa vart samla inn som ein lekk i M\xc3\xa5lfrid-prosjektet, der Nasjonalbiblioteket p\xc3\xa5 vegner av Kulturdepartementet og i samarbeid med Spr\xc3\xa5kr\xc3\xa5det haustar og aggregerer tekstdata for \xc3\xa5 dokumentere bruken av bokm\xc3\xa5l og nynorsk hj\xc3\xa5 statlege institusjonar.</p><p>Spr\xc3\xa5kbanken f\xc3\xb8retok ei fokusert hausting av nettsidene til dei aktuelle institusjonane mellom desember 2023 og januar 2024. Tekstdokument (HTML, DOC(X)/ODT og PDF) vart lasta ned rekursivt fr\xc3\xa5 dei ulike domena, 12 niv\xc3\xa5 ned p\xc3\xa5 nettsidene. Me tok \xc3\xa5lmenne h\xc3\xb8flegheitsomsyn og respekterte robots.txt.</p></article></main><footer><p>Organisasjonsnummer 976 029 100</p></footer></body></html>'

@pytest.fixture
def html_encoding_declaration_invalid_bytestring_text_content():
    """ Will return as windows-1252, ideally we should use errors=replace here """
    return 'Nasjonalbiblioteket: SprÃ¥kbankens ressurskatalogNasjonalbiblioteket: SprÃ¥kbankens ressurskatalogSprÃ¥kbankenNyhendeRessurskatalogenOm SprÃ¥kbankenRessurskatalogenCLARINOFelles datakatalogMøfrid 2024 â€“ Fritt tilgjengelege tekster frÃ¥ norske statlege nettsiderDette korpuset inneheld dokument frÃ¥ 497 internettdomene tilknytta norske statlege institusjonar. Totalt bestÃ¥r materialet av omlag 2,6 milliardar Â«tokensÂ» (ord og teiknsetting). I tillegg til tekster pÃ¥ bokmÃ¥l og nynorsk inneheld korpuset tekster pÃ¥ nordsamisk, lulesamisk, sÃ¸rsamisk og engelsk.Dataa vart samla inn som ein lekk i MÃ¥lfrid-prosjektet, der Nasjonalbiblioteket pÃ¥ vegner av Kulturdepartementet og i samarbeid med SprÃ¥krÃ¥det haustar og aggregerer tekstdata for Ã¥ dokumentere bruken av bokmÃ¥l og nynorsk hjÃ¥ statlege institusjonar.SprÃ¥kbanken fÃ¸retok ei fokusert hausting av nettsidene til dei aktuelle institusjonane mellom desember 2023 og januar 2024. Tekstdokument (HTML, DOC(X)/ODT og PDF) vart lasta ned rekursivt frÃ¥ dei ulike domena, 12 nivÃ¥ ned pÃ¥ nettsidene. Me tok Ã¥lmenne hÃ¸flegheitsomsyn og respekterte robots.txt.Organisasjonsnummer 976 029 100'

@pytest.fixture
def xhtml_unicode_string_with_encoding_declaration():
    """ A UTF-8 byte string with XHTML and encoding declaration """
    return """<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"><html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en"><head><title>Eksempel-XHTML fra Nasjonalbiblioteket</title><meta http-equiv="Content-Type" content="text/html; charset=UTF-8" /><meta property="og:site_name" content="Nasjonalbiblioteket" /</head><body><p>Hello, world! – med UTF-kodering.</p></body></html>""".encode("utf-8")

@pytest.fixture
def xhtml_unicode_string_with_encoding_declaration_text_content():
    return "Eksempel-XHTML fra NasjonalbiblioteketHello, world! – med UTF-kodering."

@pytest.fixture
def xhtml_unicode_string_with_wrong_encoding_declaration():
    """ A UTF-8 byte string with XHTML and wrong encoding declaration """
    return """<?xml version="1.0" encoding="ISO-8859-1"?><!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"><html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en"><head><title>Eksempel-XHTML frå Nasjonalbiblioteket</title><meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1" /><meta property="og:site_name" content="Nasjonalbiblioteket" /</head><body><p>Hello, world! — med ISO‑8859‑1-kodering.</p></body></html>""".encode("utf-8")

@pytest.fixture
def xhtml_unicode_string_with_wrong_encoding_declaration_text_content():
    return "Eksempel-XHTML frå NasjonalbiblioteketHello, world! — med ISO‑8859‑1-kodering."

@pytest.fixture
def links_in_html():
    """ Absolute and relative links in valid HTML """
    return "<html><body><div>Here is <a href='https://www.nb.no/search'>a</a> link. There is <a href='/sprakbanken'>another one</a>.</div></body></html>".encode("utf-8")

@pytest.fixture
def html_with_boilerplate():
    """ A valid HTML document with article-like text in Norwegian Nynorsk among boilerplate """
    return """<!DOCTYPE html><html lang="nn"><head><meta charset="UTF-8"><meta property="og:site_name" content="Nasjonalbiblioteket"><meta property="article:modified_time" content="2025-09-30T09:14:25+00:00"><title>Nasjonalbiblioteket: Språkbankens ressurskatalog</title></head><body><header><h1>Nasjonalbiblioteket: Språkbankens ressurskatalog</h1><nav><ul><li><a href="#">Språkbanken</a></li><li><a href="#">Nyhende</a></li><li><a href="#">Ressurskatalogen</a></li><li><a href="#">Om Språkbanken</a></li></ul></nav></header><aside><h3>Ressurskatalogen</h3><ul><li><a href="#">CLARINO</a></li><li><a href="#">Felles datakatalog</a></li></ul></aside><main><article><h2>Målfrid 2024 – Fritt tilgjengelege tekster frå norske statlege nettsider</h2><p>Dette korpuset inneheld dokument frå 497 internettdomene tilknytta norske statlege institusjonar. Totalt består materialet av omlag 2,6 milliardar «tokens» (ord og teiknsetting). I tillegg til tekster på bokmål og nynorsk inneheld korpuset tekster på nordsamisk, lulesamisk, sørsamisk og engelsk.</p><p>Dataa vart samla inn som ein lekk i Målfrid-prosjektet, der Nasjonalbiblioteket på vegner av Kulturdepartementet og i samarbeid med Språkrådet haustar og aggregerer tekstdata for å dokumentere bruken av bokmål og nynorsk hjå statlege institusjonar.</p><p>Språkbanken føretok ei fokusert hausting av nettsidene til dei aktuelle institusjonane mellom desember 2023 og januar 2024. Tekstdokument (HTML, DOC(X)/ODT og PDF) vart lasta ned rekursivt frå dei ulike domena, 12 nivå ned på nettsidene. Me tok ålmenne høflegheitsomsyn og respekterte robots.txt.</p></article></main><footer><p>Organisasjonsnummer 976 029 100</p></footer></body></html>""".encode("utf-8")
