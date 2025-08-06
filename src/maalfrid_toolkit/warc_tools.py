import argparse
from maalfrid_toolkit.notram_avisleser import get_text_fitz
import maalfrid_toolkit.htmlclean as htmlclean
import maalfrid_toolkit.msword
from maalfrid_toolkit.utils import convert_encoding, return_all_stop_words
from maalfrid_toolkit.simhash_docs import compute_simhash
from warcio.recordloader import ArcWarcRecord
from warcio.archiveiterator import ArchiveIterator
from warcio.warcwriter import WARCWriter
from warcio.statusandheaders import StatusAndHeaders
from pathlib import Path
from io import BytesIO
import hashlib
import uuid
import requests

stop_words = return_all_stop_words()

class MaalfridWarcRecord(ArcWarcRecord):
    def __init__(self, *args, **kwargs):
        self.warc_file_id = kwargs.pop('warc_file_id', None)
        self.warc_file_name = kwargs.pop('warc_file_name', None)
        self.use_lenient_html_parser = kwargs.pop('use_lenient_html_parser', False)
        self.calculate_simhash = kwargs.pop('calculate_simhash', False)
        super(MaalfridWarcRecord, self).__init__(*args, **kwargs)
        self.url = self.rec_headers.get('WARC-Target-URI')
        self.content_type = ''
        self.title = None
        self.metadata = None
        self.full_text = None
        self.full_text_hash = None
        self.content = None
        self.content_hash = None
        self.simhash_value = None
        self.simhash_value_bit = None
        self._get_content_type()
        self._read_content()
        self._get_content_hash()

    def _get_content_type(self):
        try:
            if self.rec_type == 'response':
                self.content_type = self.http_headers.get('Content-Type')
            elif self.rec_type == 'resource' and self.url.startswith("urn:dom"):
                self.content_type = self.rec_headers.get('Content-Type')
        except:
            pass

    def _read_content(self):
        try:
            self.content = self.content_stream().read()
        except:
            print("problem reading content stream... skipping", self.rec_headers.get('WARC-Record-ID'))

    def _get_content_hash(self):
        if self.content != None:
            self.content_hash = hashlib.sha1(self.content).hexdigest()

    def _get_simhash(self):
        # only create simhashes of documents with at least one paragraph
        if self.full_text != None:
            if len(self.full_text) > 0:
                try:
                    fulltext_id, self.simhash_value, self.simhash_value_bit = compute_simhash(fulltext_id=self.full_text_hash, doc='\n'.join(self.full_text))
                except Exception as e:
                    print("could not create simhash... simhash will be None", self.rec_headers.get('WARC-Record-ID'))
                    pass

    def _extract_full_text(self):
        if self.content != None:
            if self.content_type.startswith("text/html"):
                try:
                    utf_stream = convert_encoding(self.content)
                    tree = htmlclean.get_lxml_tree(utf_stream, use_lenient_html_parser=self.use_lenient_html_parser)

                    # extract document title and metadata
                    self.title = htmlclean.get_title(tree)
                    self.metadata = htmlclean.get_metadata(tree)

                    # extract fulltext
                    self.full_text = htmlclean.removeBP(tree, stop_words=stop_words)
                except Exception as e:
                    print("problem loading HTML... skipping", self.rec_headers.get('WARC-Record-ID'), self.warc_file_name)
            elif self.content_type.startswith("application/msword") or self.content_type.startswith("application/vnd.openxmlformats-officedocument.wordprocessingml.document") or self.content_type.startswith("application/vnd.oasis.opendocument.text-master"):
                try:
                    urn = self.rec_headers.get('WARC-Record-ID')
                    text = maalfrid_toolkit.msword.extract_doc(urn=urn, content_stream=self.content, mime_type=self.http_headers.get('Content-Type'))
                    if text != None:
                        self.full_text = text.split("\n")
                except Exception as e:
                    print("problem loading DOC... skipping", self.rec_headers.get('WARC-Record-ID'), self.warc_file_name)
            elif self.content_type.startswith("application/pdf"):
                try:
                    pdf_stream = BytesIO(self.content)
                    text, html = get_text_fitz(contents=pdf_stream, filename=Path("dummy.pdf"))
                    if text != None:
                        # Postgres does not handle the NULL character (\x00), replace it with "replacement character"
                        # https://github.com/cms-dev/cms/issues/888
                        self.full_text = text.replace("\x00", "\uFFFD")
                        self.full_text = self.full_text.split("\n")
                except Exception as e:
                    print("problem loading PDF... skipping", self.rec_headers.get('WARC-Record-ID'), self.warc_file_name)

    def _get_full_text_hash(self):
        if self.full_text != None:
            self.full_text_hash = hashlib.sha1('\n'.join(self.full_text).encode("utf-8")).hexdigest()

    def extract_full_text(self):
        """ RUn out full-text extraction """
        self._extract_full_text()
        self._get_full_text_hash()

        if self.calculate_simhash == True:
            self._get_simhash()

    def to_dict(self):
        return {'url': self.url, 'date': self.rec_headers.get('WARC-Date'), 'content_type': self.content_type, 'title': self.title, 'metadata': self.metadata, 'fulltext': self.full_text, 'full_text_hash': self.full_text_hash, "simhash": self.simhash_value if self.calculate_simhash == True else None}

def convert_to_maalfrid_record(arc_warc_record, warc_file_id=None, warc_file_name=None, use_lenient_html_parser=False, calculate_simhash=False):
    return MaalfridWarcRecord(arc_warc_record.format, arc_warc_record.rec_type, arc_warc_record.rec_headers, arc_warc_record.raw_stream, arc_warc_record.http_headers, arc_warc_record.content_type, arc_warc_record.length, warc_file_id=warc_file_id, warc_file_name=warc_file_name, use_lenient_html_parser=use_lenient_html_parser, calculate_simhash=calculate_simhash)

def make_request(url):
    try:
        response = requests.get(url)
    except:
        response = None
        
    return response

def create_record(url, response):
    # Initialize the WARC writer 
    warc_stream = BytesIO()
    writer = WARCWriter(warc_stream, gzip=True)
    warc_record_id = f'<urn:uuid:{uuid.uuid4()}>'

    warc_headers_dict = { 'WARC-Target-URI': url, 'WARC-Record-ID': warc_record_id }
    
    http_headers = StatusAndHeaders('200 OK', response.headers.items(), protocol='HTTP/1.1')

    # Create a WARC record
    warc_record = writer.create_warc_record(
        url,
        'response',
        payload=BytesIO(response.content),
        warc_content_type=response.headers.get('Content-Type', 'application/octet-stream'),
        warc_headers_dict=warc_headers_dict,
        http_headers=http_headers
    )
    
    return warc_record

def warc_dedup(files):
    """ Dedup WARCs with duplicate WARC-Record-IDs (typically produced by Browsertrix) """
    warc_ids = set()

    for file in files:
        if file.endswith('warc.gz') and not file.endswith('meta.warc.gz'):
            print(file)
            path = Path(file)
            base_name = path.name.split(".")[0]
            newfile = path.with_name(f"{base_name}_dedup.warc.gz")
            with open(file, 'rb') as stream:
                with open(newfile, 'wb') as fh:
                    warc_writer = WARCWriter(fh)
                    try:
                        for record in ArchiveIterator(stream):
                            warc_record_id = record.rec_headers.get('WARC-Record-ID')
                            if warc_record_id in warc_ids:
                                print(file, warc_record_id, "is duplicated")
                            else:
                                warc_ids.add(warc_record_id)
                                # write the WARC record to the new file
                                warc_writer.write_record(record)
                    except:
                        print("error in ", file)
                        pass

def filter_warc(stream, content_types=["text/html"], arc2warc=False):
    for record in ArchiveIterator(stream, arc2warc=arc2warc):
        # filter only status_code 200 responses
        if record.rec_type == 'response':
            mime = record.http_headers.get('Content-Type')

            if mime:
                for content_type in content_types:
                    if mime.startswith(content_type):
                        statusline = record.http_headers.statusline
                        if statusline:
                            if statusline.startswith('200'):
                                yield record
        elif record.rec_type == 'resource' and "text/html" in content_types:
            url = record.rec_headers.get('WARC-Target-URI')
            if url:
                if url.startswith("urn:dom"):
                    if record.rec_headers.get('Content-Type').startswith("text/html"):
                        yield record

def count_filtered_records(stream, content_types=["text/html"], arc2warc=False):
    count = 0
    for _ in filter_warc(stream, content_types, arc2warc=arc2warc):
        count += 1
    return count

def main():
    # Parse commandline
    parser = argparse.ArgumentParser(
        description="Målfrid WARC tools")

    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    parser_ls = subparsers.add_parser("ls", help="Iterate over and list the contents of a WARC file.")
    parser_browsertrix_dedup = subparsers.add_parser("browsertrix_dedup", help="Validate and deduplicate the contents of one or more WARC files produced by browsertrix.")

    parser_ls.add_argument("--file", type=str, help="Path to WARC file.")
    parser_browsertrix_dedup.add_argument("--files", type=str, nargs='+', help="Paths to the WARC files.")

    args = parser.parse_args()

    if args.command:
        if args.command == "ls":
            if args.file.endswith('warc.gz') or args.file.endswith('warc'):
                with open(args.file, 'rb') as stream:
                    for record in filter_warc(stream):
                        maalfrid_record = convert_to_maalfrid_record(record, warc_file_name=args.file)
                        if maalfrid_record:
                            print(maalfrid_record.warc_file_name, maalfrid_record.url, maalfrid_record.content_hash, maalfrid_record.full_text_hash)
                        else:
                            pass
        elif args.command == "browsertrix_dedup":
            warc_dedup(args.files)
            pass
    else:
        parser.print_help()

if __name__ == '__main__':
    main()