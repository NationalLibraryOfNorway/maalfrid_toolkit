import sys
import argparse
from pathlib import Path
import hashlib
import maalfrid_toolkit.config as c
import maalfrid_toolkit.crawl as crawl
import maalfrid_toolkit.warc_tools as wt
import maalfrid_toolkit.langdet as langdet
import maalfrid_toolkit.htmlclean as htmlclean
from maalfrid_toolkit.utils import convert_encoding, return_all_stop_words
import json
import time

stop_words = return_all_stop_words()
hashes = set()

def create_document(paragraphs, langStr):
    rows = []
    docId = langStr[0]
    lang_classifications = json.loads(langStr[2])
    for idx, line in enumerate(paragraphs):
        rows.append([line, lang_classifications[str(idx)]["tokens"], lang_classifications[str(idx)]["lang"]])
    return rows

def aggregate_statistics(langStr):
    lang_classifications = json.loads(langStr[2])
    nob = 0
    nno = 0
    eng = 0
    other = 0

    for key in lang_classifications:
        lang_class = lang_classifications[key]
        if lang_class["lang"] == "nob":
            nob += lang_class["tokens"]
        elif lang_class["lang"] == "nno":
            nno += lang_class["tokens"]
        elif lang_class["lang"] == "eng":
            eng += lang_class["tokens"]
        else:
            other += lang_class["tokens"]

    return [nob, nno, eng, other]

def aggregate_all(rows):
    nob = 0
    nno = 0
    eng = 0
    other = 0

    for row in rows:
        nob += row[0]
        nno += row[1]
        eng += row[2]
        other += row[3]

    nor = nob + nno

    if nor > 0 and nno > 0:
        nno_percent = str(round((nno / nor) * 100, 2)) + " %"
    else:
        nno_percent = "0 %"

    results =  {'nor': nor, 'nob': nob, 'nno': nno, 'eng': eng, 'other': other, 'nno_percent': nno_percent}

    print("# Statistics")
    print("Norwegian:", results["nor"])
    print("- Bokmål:", results["nob"])
    print("- Nynorsk:", results["nno"])
    print("=", results["nno_percent"], "nynorsk")
    print("")
    print("English:", results["eng"])
    print("Other:", results["other"])    

def print_rows(rows):
    print("sentence".ljust(50), "tokens", "language", sep="\t")
    for row in rows:
        print(row[0][:50].ljust(50), row[1], row[2], sep="\t")

def document_pipeline(record):
    if not args.to_jsonl:
        print(record.url)
    
    if record.content:
        if record.full_text:
            langStr = langdet.langdet(docId=record.url, paras=record.full_text, apply_language_filter=True, engine=args.lid_engine)
            rows = create_document(paragraphs=record.full_text, langStr=langStr)
            if args.verbose:
                print_rows(rows)
                print("\n")
            elif args.to_jsonl:
                jsonl = record.to_dict()
                jsonl["lang"] = langStr[1]
                print(json.dumps(jsonl))
            return langStr
        elif isinstance(record.full_text, list) and not args.to_jsonl:
            print("No content left after boilerplate removal!\n")
        elif record.full_text == None and not args.to_jsonl:
            print("Content could not be extracted.")
    else:
        print("No content to parse.\n")

    return None

def process_url(url, args):
    response = wt.make_request(url)
    if response:
        record = wt.create_record(url, response)
        maalfrid_record = wt.convert_to_maalfrid_record(record, use_lenient_html_parser=args.use_lenient_html_parser, calculate_simhash=args.calculate_simhash)
        maalfrid_record.extract_full_text()
        langStr = document_pipeline(maalfrid_record)
        if langStr:
            return aggregate_statistics(langStr)

def parse_args():
    # Parse commandline
    parser = argparse.ArgumentParser(
        description="Run the Målfrid pipeline on a single URL or on a WARC file")
    parser.add_argument('--url', type=str, help='A URL to process')
    parser.add_argument('--warc_file', type=str, help='Path to a WARC file')
    parser.add_argument('--crawl_sitemap', action='store_true', help='Use the URL as a seed for crawling (should point to a sitemap)')
    parser.add_argument('--use_lenient_html_parser', action='store_true', help="Use a lenient HTML parser to fix broken HTML (more expensive).")
    parser.add_argument('--calculate_simhash', action='store_true', help="Calculate simhash for each record.")
    parser.add_argument('--dedup', action='store_true', help='Do not count exact text duplicates (when using WARC file)')
    parser.add_argument('--content_type', type=str, help='Content type to filter on')
    parser.add_argument('--lid_engine', type=str, default="textcat", help='Default engine for language identification')
    parser.add_argument('--verbose', action='store_true', help="Print language statistics for each response.")
    parser.add_argument('--to_jsonl', action='store_true', help="Dump result as JSONL to STDOUT.")
    args = parser.parse_args()

    if not args.url and not args.warc_file:
        args.url = input("Please enter a valid URL: ")

    return args

def run(args):
    rows = []

    if args.url:
        url = args.url
        if args.crawl_sitemap:
            print("Crawling sitemap", args.url)
            urls = crawl.sitemap_crawler(args.url)
            for url in urls:
                row = process_url(url, args)
                time.sleep(2)
                if row:
                    rows.append(row)
        else:
            row = process_url(url, args)
            if row:
                rows.append(row)

    elif args.warc_file:
        if args.warc_file.endswith('warc.gz') and not args.warc_file.endswith('meta.warc.gz'):
            with open(args.warc_file, 'rb') as stream:
                # optional override of content types
                if args.content_type:
                    content_types = [args.content_type]
                else:
                    content_types = c.SUPPORTED_CONTENT_TYPES
                    
                for record in wt.filter_warc(stream, content_types):
                    maalfrid_record = wt.convert_to_maalfrid_record(record, warc_file_name=args.warc_file, use_lenient_html_parser=args.use_lenient_html_parser, calculate_simhash=args.calculate_simhash)
                    maalfrid_record.extract_full_text()
                    if args.dedup == True:
                        if maalfrid_record.full_text_hash in hashes:
                            continue
                        else:
                            hashes.add(maalfrid_record.full_text_hash)
                            pass

                    langStr = document_pipeline(maalfrid_record)
                    if langStr:
                        rows.append(aggregate_statistics(langStr))

    if not args.to_jsonl:
        aggregate_all(rows)

if __name__ == '__main__':
    args = parse_args()
    run(args)
