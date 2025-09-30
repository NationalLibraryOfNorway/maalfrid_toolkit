import requests
import html5lib
from html5lib.constants import DataLossWarning
import lxml.html
import justext
import warnings
from maalfrid_toolkit.utils import detect_and_decode, return_all_stop_words
from urllib.parse import urljoin, urlparse
import maalfrid_toolkit.config as c
import sys

def get_html(url):
    response = requests.get(url)

    if response.status_code == 200:
        return response.content
    else:
        return None

def get_lxml_tree(utf_stream, use_lenient_html_parser=False):
    """ Takes a binary string, return a lxml tree for justext (optional: Use a lenient parser to fix broken HTML) """

    utf_string = detect_and_decode(utf_stream)

    if use_lenient_html_parser == True:
        # ignore XHTML to HTML conversion warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DataLossWarning)
            valid_html = html5lib.parse(utf_string, treebuilder="lxml", namespaceHTMLElements=False)

        valid_html_string = lxml.html.tostring(valid_html, encoding="utf-8").decode("utf-8")
        tree = lxml.html.fromstring(valid_html_string)
    else:
        # if XHTML and containing encoding declaration, lxml.html.fromstring will raise
        # a ValuError if given a utf8 string: in that case, pass the original binary stream and decode using the encoding declaration
        try:
            tree = lxml.html.fromstring(utf_string)
        except ValueError:
            tree = lxml.html.fromstring(utf_stream)
    return tree

def get_title(tree):
    """ Get the title of the HTML document """
    title = tree.xpath("//title/text()")
    title_text = title[0].strip() if title else None
    return title_text

def get_metadata(tree):
    """ Get other metadata from the HTML document """
    meta_tags = {}
    for meta in tree.xpath("//meta[@name and @content]"):
        name = meta.attrib["name"]
        content = meta.attrib["content"]
        meta_tags[name] = content

    return meta_tags

def get_links(html, this_url):
    """ Extract links from a HTML page """
    found_links = []

    links = html.xpath("//a[@href]")

    for link in links:
        content = link.get('href')
        anchor = link.text.strip()
        anchor = anchor.replace('\n', '')
        anchor = anchor.replace('\r', '')

        url = urlparse(content)

        if url.geturl() == b"":  # happens when there is no href or src attribute
            continue
        elif url.scheme in ["http", "https"]:
            target = url.geturl()
        elif url.netloc == "":
            target = urljoin(this_url, url.path)
        else:
            continue

        # save the found connection and its type
        if "robots.txt" not in target and "mailto" not in target:
            found_links.append((target, anchor))

    return found_links

def removeBP(lxml_tree, stop_words):
    """ Expects a lxml tree and a stop words list """
    if lxml_tree is not None:
        paragraphs = justext.justext(lxml_tree, stop_words, encoding='utf-8', length_low=c.LENGTH_LOW, length_high=c.LENGTH_HIGH, stopwords_low=c.STOPWORDS_LOW, stopwords_high=c.STOPWORDS_HIGH, max_link_density=c.MAX_LINK_DENSITY, max_heading_distance=c.MAX_HEADING_DISTANCE, no_headings=c.NO_HEADINGS)
        return [paragraph["text"] for paragraph in paragraphs if paragraph["class"] == "good"]
    else:
        return ['']

def run():
    stop_words = return_all_stop_words()
    url = sys.argv[1]
    content_stream = get_html(url)
    if content_stream:
        tree = get_lxml_tree(content_stream)
        links = get_links(tree, url)
        blocks = removeBP(tree, stop_words=stop_words)
        blocks = "\n".join(blocks)
        print(tree)
        print(blocks)
        print("\n")
        print(links)
    else:
        print("URL does not give a valid response (= other than 200).")

if __name__ == '__main__':
    run()
