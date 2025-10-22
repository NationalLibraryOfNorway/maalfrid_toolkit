import pytest
from maalfrid_toolkit.utils import return_all_stop_words
import maalfrid_toolkit.htmlclean as htmlclean

def test_get_lxml_tree_with_broken_html(broken_html):
    """ LXML/Html5lib should be able to deal with (somewhat) broken HTML"""
    parsed_html = htmlclean.get_lxml_tree(broken_html, use_lenient_html_parser=False)
    parsed_html_lenient = htmlclean.get_lxml_tree(broken_html, use_lenient_html_parser=True)

    # ensure function got the h1 element right
    assert parsed_html.xpath('//h1')[0].text == "Hello World"
    assert parsed_html_lenient.xpath('//h1')[0].text == "Hello World"

def test_get_lxml_tree_with_string():
    """ get_lxml_tree() should ONLY accept byte strings """
    html_str = "<html><body><p>Hello</p></body></html>"
    with pytest.raises(TypeError):
        htmlclean.get_lxml_tree(html_str)

def test_get_lxml_tree_wrong_decoding_declaration(html_wrong_encoding_declaration, html_wrong_encoding_declaration_text_content):
    parsed_html = htmlclean.get_lxml_tree(html_wrong_encoding_declaration, use_lenient_html_parser=False)
    parsed_html_lenient = htmlclean.get_lxml_tree(html_wrong_encoding_declaration, use_lenient_html_parser=True)

    # ensure LXML.html.fromstring does not try to use the faulty encoding declaration
    assert parsed_html.text_content() == html_wrong_encoding_declaration_text_content
    assert parsed_html_lenient.text_content() == html_wrong_encoding_declaration_text_content

def test_get_lxml_tree_with_xhtml_encoding_declaration(xhtml_unicode_string_with_encoding_declaration, xhtml_unicode_string_with_encoding_declaration_text_content):
    parsed_html = htmlclean.get_lxml_tree(xhtml_unicode_string_with_encoding_declaration, use_lenient_html_parser=False)
    parsed_html_lenient = htmlclean.get_lxml_tree(xhtml_unicode_string_with_encoding_declaration, use_lenient_html_parser=True)
    assert parsed_html.text_content() == xhtml_unicode_string_with_encoding_declaration_text_content
    assert parsed_html_lenient.text_content() == xhtml_unicode_string_with_encoding_declaration_text_content

def test_get_lxml_tree_with_xhtml_wrong_encoding_declaration(xhtml_unicode_string_with_wrong_encoding_declaration, xhtml_unicode_string_with_wrong_encoding_declaration_text_content):
    parsed_html = htmlclean.get_lxml_tree(xhtml_unicode_string_with_wrong_encoding_declaration, use_lenient_html_parser=False)
    parsed_html_lenient = htmlclean.get_lxml_tree(xhtml_unicode_string_with_wrong_encoding_declaration, use_lenient_html_parser=True)
    assert parsed_html.text_content() == xhtml_unicode_string_with_wrong_encoding_declaration_text_content
    assert parsed_html_lenient.text_content() == xhtml_unicode_string_with_wrong_encoding_declaration_text_content

def test_get_lxml_tree_with_html_encoding_invalid_bytestring(html_encoding_declaration_invalid_bytestring, html_encoding_declaration_invalid_bytestring_text_content):
    parsed_html = htmlclean.get_lxml_tree(html_encoding_declaration_invalid_bytestring, use_lenient_html_parser=False)
    parsed_html_lenient = htmlclean.get_lxml_tree(html_encoding_declaration_invalid_bytestring, use_lenient_html_parser=True)
    assert parsed_html.text_content() == html_encoding_declaration_invalid_bytestring_text_content
    assert parsed_html_lenient.text_content() == html_encoding_declaration_invalid_bytestring_text_content

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

