import requests
from bs4 import BeautifulSoup
import justext
from maalfrid_toolkit.utils import convert_encoding, return_all_stop_words
from urllib.parse import urljoin, urlparse
import maalfrid_toolkit.config as c
import sys

def get_html(url):
    response = requests.get(url)

    if response.status_code == 200:
        return response.content
    else:
        return None

def ensure_valid_html(utf_stream):
    """ Use a lenient parser to fix broken HTML """
    utf_stream = BeautifulSoup(utf_stream, "html5lib")
    return utf_stream

def get_links(html, this_url):
    """ Extract links from a HTML page """
    found_links = []

    links = html.findAll('a')
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

def removeBP(utf_stream, stop_words):
    """ Expects a content_stream encoded as UTF-8 and a stop words list """
    if utf_stream:
        paragraphs = justext.justext(utf_stream, stop_words, encoding='utf-8', length_low=c.LENGTH_LOW, length_high=c.LENGTH_HIGH, stopwords_low=c.STOPWORDS_LOW, stopwords_high=c.STOPWORDS_HIGH, max_link_density=c.MAX_LINK_DENSITY, max_heading_distance=c.MAX_HEADING_DISTANCE, no_headings=c.NO_HEADINGS)
        return [paragraph["text"] for paragraph in paragraphs if paragraph["class"] == "good"]
    else:
        return ['']

def run():
    stop_words = return_all_stop_words()
    url = sys.argv[1]
    content_stream = get_html(url)
    if content_stream:
        utf_stream = convert_encoding(content_stream)
        valid_html = ensure_valid_html(utf_stream)
        links = get_links(valid_html, url)
        blocks = removeBP(valid_html.encode("utf-8"), stop_words=stop_words)
        blocks = "\n".join(blocks)
        print(blocks)
        print("\n")
        print(links)
    else:
        print("URL does not give a valid response (= other than 200).")

if __name__ == '__main__':
    run()
