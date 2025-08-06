# Copyright (c) 2011 Jan Pomikalek
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
from __future__ import print_function

import codecs
import os
import pkgutil
import re
import sys

from xml.sax.handler import ContentHandler

import lxml.etree
import lxml.html
import lxml.sax

MAX_LINK_DENSITY_DEFAULT = 0.2
LENGTH_LOW_DEFAULT = 70
LENGTH_HIGH_DEFAULT = 200
STOPWORDS_LOW_DEFAULT = 0.30
STOPWORDS_HIGH_DEFAULT = 0.32
NO_HEADINGS_DEFAULT = False
# Short and near-good headings within MAX_HEADING_DISTANCE characters before
# a good paragraph are classified as good unless --no-headings is specified.
MAX_HEADING_DISTANCE_DEFAULT = 200
#Maximum distance (in paragraphs) of a short paragraph from a good paragraph
#to re-classify the short paragraph as good.
MAX_GOOD_DISTANCE_DEFAULT = 5
PARAGRAPH_TAGS = ['blockquote', 'caption', 'center', 'col', 'colgroup', 'dd',
        'div', 'dl', 'dt', 'fieldset', 'form', 'legend', 'optgroup', 'option',
        'p', 'pre', 'table', 'td', 'textarea', 'tfoot', 'th', 'thead', 'tr',
        'ul', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
DEFAULT_ENCODING = 'utf-8'
DEFAULT_ENC_ERRORS = 'replace'
WHITE_SPACE_RE = re.compile('(?:\s|\xc2\xa0)+', re.UNICODE)
#Python2 RE do not match no-break space using \s

class JustextError(Exception):
    "Base class for jusText exceptions."

class JustextInvalidOptions(JustextError):
    pass

def get_stoplists():
    "Returns a list of inbuilt stoplists."
    stoplists = []
    stoplists_dir = os.path.join(
        os.path.dirname(sys.modules['justext'].__file__), 'stoplists')
    for filename in os.listdir(stoplists_dir):
        if filename.endswith('.txt'):
            stoplists.append(filename.rsplit('.', 1)[0])
    return stoplists

def get_stoplist(language):
    "Returns an inbuilt stoplist for the language as a set of words."
    stoplist_contents = pkgutil.get_data('justext',
        os.path.join('stoplists', language + '.txt')).decode('utf-8')
    return set(l.strip().lower() for l in stoplist_contents.split(u'\n'))

def decode_html(html_string, encoding=None, default_encoding=DEFAULT_ENCODING,
        errors=DEFAULT_ENC_ERRORS):
    """
    Converts a string containing an HTML page (html_string) into unicode.
    Tries to guess character encoding from meta tags.
    """
    if encoding:
        return html_string.decode(encoding, errors=errors)
    re_meta1 = re.compile(b'''<meta\s+http-equiv=['"]?content-type['"]?\s+content=['"]?[^'"]*charset=([^'"]+)''', re.I)
    re_meta2 = re.compile(b'''<meta\s+content=['"]?[^'"]*charset=([^'"]+)['"]?\s+http-equiv=['"]?content-type['"]?''', re.I)
    re_meta3 = re.compile(b'''<meta\s+http-equiv=['"]?charset['"]?\s+content=['"]?([^'"]+)''', re.I)
    re_meta4 = re.compile(b'''<meta\s+content=['"]?([^'"]+)['"]?\s+http-equiv=['"]?charset['"]?''', re.I)
    re_meta5 = re.compile(b'''<meta\s+charset=['"]?([^'"]+)''', re.I)
    for re_meta in (re_meta1, re_meta2, re_meta3, re_meta4, re_meta5):
        m = re_meta.search(html_string)
        if m:
            meta_encoding = m.group(1).decode('ascii')
            try:
                return html_string.decode(meta_encoding, errors=errors)
            except LookupError:
                # if the encoding specified in <meta> is unknown
                # proceed as if it wasn't found at all
                pass
    try:
        # if unknown encoding, try utf-8 first
        return html_string.decode('utf-8', errors='strict')
    except UnicodeDecodeError:
        # use default encoding if utf-8 failed
        try:
            return html_string.decode(default_encoding, errors=errors)
        except UnicodeDecodeError as e:
            raise JustextError('Unable to convert the HTML to unicode from %s: %s' % (
                default_encoding, e))

decode_entities_pp_trans = {
    ord(u'\x83'): u'\u0192',
    ord(u'\x84'): u'\u201e',
    ord(u'\x85'): u'\u2026',
    ord(u'\x86'): u'\u2020',
    ord(u'\x87'): u'\u2021',
    ord(u'\x88'): u'\u02c6',
    ord(u'\x89'): u'\u2030',
    ord(u'\x8a'): u'\u0160',
    ord(u'\x8b'): u'\u2039',
    ord(u'\x8c'): u'\u0152',
    ord(u'\x91'): u'\u2018',
    ord(u'\x92'): u'\u2019',
    ord(u'\x93'): u'\u201c',
    ord(u'\x94'): u'\u201d',
    ord(u'\x95'): u'\u2022',
    ord(u'\x96'): u'\u2013',
    ord(u'\x97'): u'\u2014',
    ord(u'\x98'): u'\u02dc',
    ord(u'\x99'): u'\u2122',
    ord(u'\x9a'): u'\u0161',
    ord(u'\x9b'): u'\u203a',
    ord(u'\x9c'): u'\u0153',
    ord(u'\x9f'): u'\u0178',
}
def decode_entities_pp(unicode_string):
    """
    Post-processing of HTML entity decoding. The entities &#128; to &#159;
    (&#x80; to &#x9f;) are not defined in HTML 4, but they are still used on
    the web and recognised by web browsers. This method converts some of the
    u'\x80' to u'\x9f' characters (which are likely to be incorrectly decoded
    entities; mostly control characters) to the characters which the entities
    are normally decoded to.
    """
    return unicode_string.translate(decode_entities_pp_trans)

def add_kw_tags(root):
    """
    Surrounds text nodes with <kw></kw> tags. To protect text nodes from
    being removed with nearby tags.
    """
    blank_text = re.compile(u'^\s*$', re.U)
    nodes_with_text = []
    nodes_with_tail = []
    for node in root.iter():
        # temporary workaround for issue #2 caused by a bug #690110 in lxml
        try:
            node.text
        except UnicodeDecodeError:
            # remove any text that can't be decoded
            node.text = ''

        if node.text and node.tag not in (lxml.etree.Comment, lxml.etree.ProcessingInstruction):
            nodes_with_text.append(node)
        if node.tail:
            nodes_with_tail.append(node)
    for node in nodes_with_text:
        kw = lxml.etree.Element('kw')
        if blank_text.match(node.text):
            kw.text = ' '
        else:
            kw.text = node.text
        node.text = None
        node.insert(0, kw)
    for node in nodes_with_tail:
        kw = lxml.etree.Element('kw')
        if blank_text.match(node.tail):
            kw.text = ' '
        else:
            kw.text = node.tail
        node.tail = None
        parent = node.getparent()
        parent.insert(parent.index(node) + 1, kw)
    return root

def remove_comments(root):
    "Removes comment nodes."
    to_be_removed = []
    for node in root.iter():
        if node.tag == lxml.etree.Comment:
            to_be_removed.append(node)
    for node in to_be_removed:
        parent = node.getparent()
        del parent[parent.index(node)]

def get_html_root(html_text, encoding=None, default_encoding=DEFAULT_ENCODING,
        enc_errors=DEFAULT_ENC_ERRORS):
    "Converts HTML text to HTML DOM root and returns the root."
    uhtml_text = decode_html(html_text, encoding, default_encoding, enc_errors)
    try:
        html_root = lxml.html.fromstring(uhtml_text)
    except ValueError: # Unicode strings with encoding declaration are not supported.
        # for XHTML files with encoding declaration, use the declared encoding
        html_root = lxml.html.fromstring(html_text)
    return html_root

def preprocess_html_root(html_root):
    "Removes unwanted parts from HTML DOM root and returns the cleaned root."
    # add <kw> tags, protect text nodes
    add_kw_tags(html_root)
    # remove comments
    remove_comments(html_root)
    # remove head, script and style
    to_be_removed = []
    for node in html_root.iter():
        if node.tag in ['head', 'script', 'noscript', 'style', 'figure', 'dialog',
                'footer', 'nav', 'canvas', 'svg', 'audio', 'embed', 'aside',
                'code', 'data', 'menu', 'object', 'picture', 'pre']:
            to_be_removed.append(node)
    for node in to_be_removed:
        parent = node.getparent()
        del parent[parent.index(node)]
    return html_root

def preprocess(html_text, encoding=None, default_encoding=DEFAULT_ENCODING,
        enc_errors=DEFAULT_ENC_ERRORS):
    "Converts HTML text to HTML DOM root, removes unwanted parts and returns the cleaned root."
    html_root = get_html_root(html_text, encoding, default_encoding, enc_errors)
    return preprocess_html_root(html_root)

class SaxPragraphMaker(ContentHandler):
    """
    A class for converting a HTML page represented as a DOM object into a list
    of paragraphs.
    """

    def __init__(self):
        self.dom = []
        self.paragraphs = []
        self.paragraph = {}
        self.link = False
        self.br = False
        self._start_new_pragraph()

    def _start_new_pragraph(self):
        if self.paragraph and self.paragraph['text_nodes'] != []:
            self.paragraph['text'] = WHITE_SPACE_RE.sub(' ', (
                ''.join(self.paragraph['text_nodes']))).strip()
            self.paragraphs.append(self.paragraph)
        self.paragraph = {
            'dom_path': '.'.join(self.dom),
            'text_nodes': [],
            'word_count': 0,
            'linked_char_count': 0,
            'tag_count': 0,
        }

    def startElementNS(self, name, qname, attrs):
        dummy_uri, name = name
        self.dom.append(name)
        if name == 'br':
            self.paragraph['text_nodes'].append(' ')
        if name in PARAGRAPH_TAGS or (name == 'br' and self.br):
            if name == 'br':
                # the <br><br> is a paragraph separator and should
                # not be included in the number of tags within the
                # paragraph
                self.paragraph['tag_count'] -= 1
            self._start_new_pragraph()
        else:
            if name == 'br':
                self.br = True
            else:
                self.br = False
            if name == 'a':
                self.link = True
            self.paragraph['tag_count'] += 1

    def endElementNS(self, name, qname):
        dummy_uri, name = name
        self.dom.pop()
        if name in PARAGRAPH_TAGS:
            self._start_new_pragraph()
        if name == 'a':
            self.link = False

    def endDocument(self):
        self._start_new_pragraph()

    def characters(self, content):
        text = WHITE_SPACE_RE.sub(' ', content)
        self.paragraph['text_nodes'].append(text)
        words = text.strip().split()
        self.paragraph['word_count'] += len(words)
        if self.link:
            self.paragraph['linked_char_count'] += len(text)
        self.br = False

def make_paragraphs(root):
    "Converts DOM into paragraphs."
    handler = SaxPragraphMaker()
    lxml.sax.saxify(root, handler)
    return [p for p in handler.paragraphs if p['text']]

def classify_paragraphs(paragraphs, stoplist, length_low=LENGTH_LOW_DEFAULT,
        length_high=LENGTH_HIGH_DEFAULT, stopwords_low=STOPWORDS_LOW_DEFAULT,
        stopwords_high=STOPWORDS_HIGH_DEFAULT, max_link_density=MAX_LINK_DENSITY_DEFAULT,
        no_headings=NO_HEADINGS_DEFAULT):
    "Context-free pragraph classification."
    for paragraph in paragraphs:
        length = len(paragraph['text'])
        stopword_count = 0
        for word in paragraph['text'].lower().split():
            if word in stoplist:
                stopword_count += 1
        word_count = paragraph['word_count']
        if word_count == 0:
            stopword_density = 0
            link_density = 0
        else:
            stopword_density = 1.0 * stopword_count / word_count
            link_density = float(paragraph['linked_char_count']) / length
        paragraph['stopword_count'] = stopword_count
        paragraph['stopword_density'] = stopword_density
        paragraph['link_density'] = link_density

        paragraph['heading'] = bool(not no_headings and re.search('(^h\d|\.h\d)', paragraph['dom_path']))
        if link_density > max_link_density:
            paragraph['cfclass'] = 'bad'
        elif (u'\xa9' in paragraph['text']) or ('&copy' in paragraph['text']):
            paragraph['cfclass'] = 'bad'
        elif re.search('(^select|\.select)', paragraph['dom_path']):
            paragraph['cfclass'] = 'bad'
        else:
            if length < length_low:
                if paragraph['linked_char_count'] > 0:
                    paragraph['cfclass'] = 'bad'
                else:
                    paragraph['cfclass'] = 'short'
            else:
                if stopword_density >= stopwords_high:
                    if length > length_high:
                        paragraph['cfclass'] = 'good'
                    else:
                        paragraph['cfclass'] = 'neargood'
                elif stopword_density >= stopwords_low:
                    paragraph['cfclass'] = 'neargood'
                else:
                    paragraph['cfclass'] = 'bad'

def _get_neighbour(i, paragraphs, ignore_neargood, inc, boundary):
    while i + inc != boundary:
        i += inc
        c = paragraphs[i]['class']
        if c in ['good', 'bad']:
            return c
        if c == 'neargood' and not ignore_neargood:
            return c
    return 'bad'

def get_prev_neighbour(i, paragraphs, max_good_distance, ignore_neargood):
    """
    Return the class of the paragraph at the top end of the short/neargood
    paragraphs block, up to max_good_distance paragraphs far. If ignore_neargood
    is True, than only 'bad' or 'good' can be returned, otherwise 'neargood'
    can be returned, too.
    """
    block_boundary = max(i - max_good_distance, -1)
    return _get_neighbour(i, paragraphs, ignore_neargood, -1, block_boundary)

def get_next_neighbour(i, paragraphs, max_good_distance, ignore_neargood):
    """
    Return the class of the paragraph at the bottom end of the short/neargood
    paragraphs block, up to max_good_distance paragraphs far. If ignore_neargood
    is True, than only 'bad' or 'good' can be returned, otherwise 'neargood'
    can be returned, too.
    """
    block_boundary = min(i + max_good_distance, len(paragraphs))
    return _get_neighbour(i, paragraphs, ignore_neargood, 1, block_boundary)

def revise_paragraph_classification(paragraphs, max_good_distance=MAX_GOOD_DISTANCE_DEFAULT,
        max_heading_distance=MAX_HEADING_DISTANCE_DEFAULT):
    """
    Context-sensitive paragraph classification. Assumes that classify_pragraphs
    has already been called.
    """
    # copy classes
    for paragraph in paragraphs:
        paragraph['class'] = paragraph['cfclass']

    # good headings
    for i, paragraph in enumerate(paragraphs):
        if not (paragraph['heading'] and paragraph['class'] == 'short'):
            continue
        j = i + 1
        distance = 0
        while j < len(paragraphs) and distance <= max_heading_distance:
            if paragraphs[j]['class'] == 'good':
                paragraph['class'] = 'neargood'
                break
            distance += len(paragraphs[j]['text'])
            j += 1

    # classify short
    new_classes = {}
    for i, paragraph in enumerate(paragraphs):
        if paragraph['class'] != 'short':
            continue
        prev_neighbour = get_prev_neighbour(i, paragraphs, max_good_distance, ignore_neargood=True)
        next_neighbour = get_next_neighbour(i, paragraphs, max_good_distance, ignore_neargood=True)
        neighbours = set((prev_neighbour, next_neighbour))
        if neighbours == set(['good']):
            new_classes[i] = 'good'
        elif neighbours == set(['bad']):
            new_classes[i] = 'bad'
        # it must be set(['good', 'bad'])
        elif (prev_neighbour == 'bad' and get_prev_neighbour(i, paragraphs, max_good_distance,
                ignore_neargood=False) == 'neargood') or \
                (next_neighbour == 'bad' and get_next_neighbour(i, paragraphs, max_good_distance,
                ignore_neargood=False) == 'neargood'):
            new_classes[i] = 'good'
        else:
            new_classes[i] = 'bad'

    for i, c in new_classes.items():
        paragraphs[i]['class'] = c

    # revise neargood
    for i, paragraph in enumerate(paragraphs):
        if paragraph['class'] != 'neargood':
            continue
        prev_neighbour = get_prev_neighbour(i, paragraphs, max_good_distance, ignore_neargood=True)
        next_neighbour = get_next_neighbour(i, paragraphs, max_good_distance, ignore_neargood=True)
        if (prev_neighbour, next_neighbour) == ('bad', 'bad'):
            paragraph['class'] = 'bad'
        else:
            paragraph['class'] = 'good'

    # more good headings
    for i, paragraph in enumerate(paragraphs):
        if not (paragraph['heading'] and paragraph['class'] == 'bad' and paragraph['cfclass'] != 'bad'):
            continue
        j = i + 1
        distance = 0
        while j < len(paragraphs) and distance <= max_heading_distance:
            if paragraphs[j]['class'] == 'good':
                paragraph['class'] = 'good'
                break
            distance += len(paragraphs[j]['text'])
            j += 1

def justext(lxml_object, stoplist, length_low=LENGTH_LOW_DEFAULT,
        length_high=LENGTH_HIGH_DEFAULT, stopwords_low=STOPWORDS_LOW_DEFAULT,
        stopwords_high=STOPWORDS_HIGH_DEFAULT, max_link_density=MAX_LINK_DENSITY_DEFAULT,
        max_good_distance=MAX_GOOD_DISTANCE_DEFAULT,
        max_heading_distance=MAX_HEADING_DISTANCE_DEFAULT, no_headings=NO_HEADINGS_DEFAULT,
        encoding=None, default_encoding=DEFAULT_ENCODING,
        enc_errors=DEFAULT_ENC_ERRORS):
    """
    Converts an HTML page into a list of classified paragraphs. Each paragraph
    is represented as a dictionary with the following attributes:
    
    text:
      Plain text content.
    
    cfclass:
      The context-free class -- class assigned by the context-free
      classification: 'good', 'bad', 'neargood' or 'short'.
    
    class:
      The final class: 'good' or 'bad'.
    
    heading:
      Set to True of the paragraph contains a heading, False otherwise.
    
    word_count:
      Number of words.
    
    linked_char_count:
      Number of characters inside links.

    link_density:
      linked_char_count / len(text)
            
    stopword_count:
      Number of stoplist words.
      
    stopword_density:
      stopword_count / word_count
    
    dom_path:
      A dom path to the paragraph in the originial HTML page.
    """

    # Adaptation for Maalfrid toolkit: skip the preprocess function (since preprocessing is done outside) and proceed directly to preprocess_html_root, expecting a lxml object

    #root = preprocess(html_text, encoding=encoding,
    #    default_encoding=default_encoding, enc_errors=enc_errors)

    root = preprocess_html_root(lxml_object)
    paragraphs = make_paragraphs(root)
    classify_paragraphs(paragraphs, stoplist, length_low, length_high,
        stopwords_low, stopwords_high, max_link_density, no_headings)
    revise_paragraph_classification(paragraphs, max_good_distance, max_heading_distance)
    return paragraphs

def html_escape(text):
    "Converts < and > to &lt; and &gt;."
    return text.replace('<', '&lt;').replace('>', '&gt;')

def output_default(paragraphs, fp, no_boilerplate=True):
    """
    Outputs the paragraphs as:
    <tag> text of the first paragraph
    <tag> text of the second paragraph
    ...
    where <tag> is <p>, <h> or <b> which indicates
    standard paragraph, heading or boilerplate respecitvely.
    """
    for paragraph in paragraphs:
        if paragraph['class'] == 'good':
            if paragraph['heading']:
                tag = 'h'
            else:
                tag = 'p'
        else:
            if no_boilerplate:
                continue
            else:
                tag = 'b'
        escaped_paragraph = html_escape(paragraph['text']).strip()
        fp.write(u'<%s> %s\n' % (tag, escaped_paragraph))

def output_detailed(paragraphs, fp):
    """
    Same as output_default, but only <p> tags are used and the following
    attributes are added: class, cfclass and heading.
    """
    for paragraph in paragraphs:
        escaped_paragraph = html_escape(paragraph['text']).strip()
        heading_str = 'yes' if paragraph['heading'] else 'no'
        fp.write(u'<p class="%s" cfclass="%s" heading="%s"> %s\n' % (
            paragraph['class'], paragraph['cfclass'],
            heading_str, escaped_paragraph))

def output_krdwrd(paragraphs, fp):
    """
    Outputs the paragraphs in a KrdWrd compatible format:
    class<TAB>first text node
    class<TAB>second text node
    ...
    where class is 1, 2 or 3 which means
    boilerplate, undecided or good respectively. Headings are output as
    undecided.
    """
    for paragraph in paragraphs:
        if paragraph['class'] in ('good', 'neargood'):
            if paragraph['heading']:
                cls = 2
            else:
                cls = 3
        else:
            cls = 1
        for text_node in paragraph['text_nodes']:
            fp.write(u'%i\t%s\n' % (cls, text_node.strip()))

def usage():
    return """Usage: %(progname)s -s STOPLIST [OPTIONS] [HTML_FILE]
Convert HTML to plain text and remove boilerplate.

  -o OUTPUT_FILE   if not specified, output is written to stdout
  --encoding=...   default character encoding to be used if not specified
                   in the HTML meta tags (default: %(default_encoding)s)
  --enc-force      force specified encoding, ignore HTML meta tags
  --enc-errors=... errors handling for character encoding conversion:
                     strict: fail on error
                     ignore: ignore characters which can't be converted
                     replace: replace characters which can't be converted
                              with U+FFFD unicode replacement characters
                   (default: %(default_enc_errors)s)
  --format=...     output format; possible values:
                     default: one paragraph per line, each preceded with
                              <p> or <h> (headings)
                     boilerplate: same as default, except for boilerplate
                                  paragraphs are included, too, preceded
                                  with <b>
                     detailed: one paragraph per line, each preceded with
                               <p> tag containing detailed information
                               about classification as attributes
                     krdwrd: KrdWrd compatible format
  --no-headings    disable special handling of headings
  --list-stoplists print a list of inbuilt stoplists and exit
  -V, --version    print version information and exit 
  -h, --help       display this help and exit

If no HTML_FILE specified, input is read from stdin.

STOPLIST must be one of the following:
  - one of the inbuilt stoplists; see:
      %(progname)s --list-stoplists
  - path to a file with the most frequent words for given language,
    one per line, in utf-8 encoding, lowercased by Justext
  - None - this activates a language-independent mode

Advanced options:
  --length-low=INT (default %(length_low)i)
  --length-high=INT (default %(length_high)i)
  --stopwords-low=FLOAT (default %(stopwords_low)f)
  --stopwords-high=FLOAT (default %(stopwords_high)f)
  --max-link-density=FLOAT (default %(max_link_density)f)
  --max-good-distance=INT (default %(max_good_distance)i)
  --max-heading-distance=INT (default %(max_heading_distance)i)
""" % {
    'progname': os.path.basename(os.path.basename(sys.argv[0])),
    'length_low': LENGTH_LOW_DEFAULT,
    'length_high': LENGTH_HIGH_DEFAULT,
    'stopwords_low': STOPWORDS_LOW_DEFAULT,
    'stopwords_high': STOPWORDS_HIGH_DEFAULT,
    'max_link_density': MAX_LINK_DENSITY_DEFAULT,
    'max_good_distance': MAX_GOOD_DISTANCE_DEFAULT,
    'max_heading_distance': MAX_HEADING_DISTANCE_DEFAULT,
    'default_encoding': DEFAULT_ENCODING,
    'default_enc_errors': DEFAULT_ENC_ERRORS,
}

def main():
    import getopt
    import io
    from justext import __version__ as VERSION

    try:
        opts, args = getopt.getopt(sys.argv[1:], "o:s:hV", ["encoding=",
            "enc-force", "enc-errors=", "format=",
            "no-headings", "help", "version", "length-low=", "length-high=",
            "stopwords-low=", "stopwords-high=", "max-link-density=",
            "max-heading-distance=", "list-stoplists"])
    except getopt.GetoptError as err:
        print(err, file=sys.stderr)
        print(usage(), file=sys.stderr)
        sys.exit(1)

    stream_writer = codecs.lookup('utf-8')[-1]
    # fp_out = stream_writer(sys.stdout)
    fp_out = io.open(sys.stdout.fileno(), 'wt', encoding='utf-8')
    stoplist = None
    format = 'default'
    no_headings = False
    length_low = LENGTH_LOW_DEFAULT
    length_high = LENGTH_HIGH_DEFAULT
    stopwords_low = STOPWORDS_LOW_DEFAULT
    stopwords_high = STOPWORDS_HIGH_DEFAULT
    max_link_density = MAX_LINK_DENSITY_DEFAULT
    max_good_distance = MAX_GOOD_DISTANCE_DEFAULT
    max_heading_distance = MAX_HEADING_DISTANCE_DEFAULT
    encoding = None
    default_encoding = DEFAULT_ENCODING
    force_default_encoding = False
    enc_errors = DEFAULT_ENC_ERRORS

    try:
        for o, a in opts:
            if o in ("-h", "--help"):
                print(usage(), file=sys.stderr)
                sys.exit(0)
            if o in ("-V", "--version"):
                print("%s: jusText v%s\n\nCopyright (c) 2011 Jan Pomikalek <jan.pomikalek@gmail.com>" % (
                    os.path.basename(sys.argv[0]), VERSION))
                sys.exit(0)
            elif o == "--list-stoplists":
                print("\n".join(get_stoplists()))
                sys.exit(0)
            elif o == "-o":
                try:
                    #fp_out = codecs.open(a, 'w', 'utf-8') # fixme
                    fp_out = codecs.open(a, 'w', 'utf-8')
                except IOError as e:
                    raise JustextInvalidOptions(
                        "Can't open %s for writing: %s" % (a, e))
            elif o == "-s":
                if a.lower() == 'none':
                    stoplist = set()
                else:
                    if os.path.isfile(a):
                        try:
                            fp_stoplist = codecs.open(a, 'r', 'utf-8')
                            stoplist = set([l.strip().lower() for l in fp_stoplist])
                            fp_stoplist.close()
                        except IOError as e:
                            raise JustextInvalidOptions(
                                "Can't open %s for reading: %s" % (a, e))
                        except UnicodeDecodeError as e:
                            raise JustextInvalidOptions(
                                "Unicode decoding error when reading " \
                                "the stoplist (probably not in utf-8): %s" % e)
                    elif a in get_stoplists():
                        stoplist = get_stoplist(a)
                    else:
                        if re.match('^\w*$', a):
                            # only alphabetical chars, probably misspelled or
                            # unsupported language
                            raise JustextInvalidOptions(
                                "Unknown stoplist: %s\nAvailable stoplists:\n%s" % (
                                    a, '\n'.join(get_stoplists())))
                        else:
                            # probably incorrectly specified path
                            raise JustextInvalidOptions("File not found: %s" % a)
            elif o == "--encoding":
                try:
                    default_encoding = a
                    u''.encode(default_encoding)
                except LookupError:
                    raise JustextInvalidOptions("Uknown character encoding: %s" % a)
            elif o == "--enc-force":
                force_default_encoding = True
            elif o == "--enc-errors":
                if a.lower() in ['strict', 'ignore', 'replace']:
                    enc_errors = a.lower()
                else:
                    raise JustextInvalidOptions("Invalid --enc-errors value: %s" % a)
            elif o == "--format":
                if a in ['default', 'boilerplate', 'detailed', 'krdwrd']:
                    format = a
                else:
                    raise JustextInvalidOptions("Uknown output format: %s" % a)
            elif o == "--no-headings":
                no_headings = True
            elif o == "--length-low":
                try:
                    length_low = int(a)
                except ValueError:
                    raise JustextInvalidOptions(
                        "Invalid value for %s: '%s'. Integer expected." % (o, a))
            elif o == "--length-high":
                try:
                    length_high = int(a)
                except ValueError:
                    raise JustextInvalidOptions(
                        "Invalid value for %s: '%s'. Integer expected." % (o, a))
            elif o == "--stopwords-low":
                try:
                    stopwords_low = float(a)
                except ValueError:
                    raise JustextInvalidOptions(
                        "Invalid value for %s: '%s'. Float expected." % (o, a))
            elif o == "--stopwords-high":
                try:
                    stopwords_high = float(a)
                except ValueError:
                    raise JustextInvalidOptions(
                        "Invalid value for %s: '%s'. Float expected." % (o, a))
            elif o == "--max-link-density":
                try:
                    max_link_density = float(a)
                except ValueError:
                    raise JustextInvalidOptions(
                        "Invalid value for %s: '%s'. Float expected." % (o, a))
            elif o == "--max-good-distance":
                try:
                    max_good_distance = int(a)
                except ValueError:
                    raise JustextInvalidOptions(
                        "Invalid value for %s: '%s'. Integer expected." % (o, a))
            elif o == "--max-heading-distance":
                try:
                    max_heading_distance = int(a)
                except ValueError:
                    raise JustextInvalidOptions(
                        "Invalid value for %s: '%s'. Integer expected." % (o, a))

        if force_default_encoding:
            encoding = default_encoding

        if stoplist is None:
            raise JustextInvalidOptions("No stoplist specified.")

        if not stoplist:
            # empty stoplist, switch to language-independent mode
            stopwords_high = 0
            stopwords_low = 0

        if args == []:
            try:
                fp_in = sys.stdin.buffer
            except:
                fp_in = sys.stdin
        else:
            try:
                fp_in = open(args[0], 'rb')
            except IOError as e:
                raise JustextInvalidOptions(
                    "Can't open %s for reading: %s" % (args[0], e))
                sys.exit(1)

        html_text = fp_in.read()
        paragraphs = justext(html_text, stoplist, length_low, length_high,
            stopwords_low, stopwords_high, max_link_density, max_good_distance,
            max_heading_distance, no_headings, encoding, default_encoding, enc_errors)
        if format == "default":
            output_default(paragraphs, fp_out)
        elif format == "boilerplate":
            output_default(paragraphs, fp_out, no_boilerplate=False)
        elif format == "detailed":
            output_detailed(paragraphs, fp_out)
        elif format == "krdwrd":
            output_krdwrd(paragraphs, fp_out)
        else:
            # this should not happen; format checked when parsing options
            raise AssertionError("Unknown format: %s" % format)

    except JustextError as e:
        print("%s: %s" % (os.path.basename(sys.argv[0]), e), file=sys.stderr)
        sys.exit(1)
