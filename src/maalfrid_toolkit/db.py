import psycopg2 as pg
from psycopg2.extras import RealDictCursor
import argparse
import maalfrid_toolkit.config as c
import maalfrid_toolkit.warc_tools as wt
import maalfrid_toolkit.langdet as langdet
from maalfrid_toolkit.simhash_docs import serialize_simhashes, build_index, compare, compute_simhash
import multiprocessing
from itertools import chain
from functools import partial
import tqdm
import time

def parse_args():
    # Parse commandline
    parser = argparse.ArgumentParser(
        description="Run the Målfrid pipeline on WARC file and insert to DB; classify documents")
    parser.add_argument('--warc_file', type=str, help='Path to a WARC file')
    parser.add_argument('--use_lenient_html_parser', action='store_true', help="Use a lenient HTML parser to fix broken HTML (more expensive).")
    parser.add_argument('--content_type', type=str, help='Content type to filter on')
    parser.add_argument('--insert_new_crawl', action="store_true", help='Insert paths from warcinfo')
    parser.add_argument('--insert_new_simhashes', action="store_true", help='Insert simhashes for new fulltexts')
    parser.add_argument('--detect_near_duplicates', action="store_true", help='Calculate simhash distances and identify near duplicates per domain and document type')
    parser.add_argument('--classify', action="store_true", help='Run document language classifier on all documents in the DB')
    parser.add_argument('--transfer_block_lists', action="store_true", help="Import block lists from last crawl")
        
    args = parser.parse_args()

    if not args.warc_file and not args.classify and not args.detect_near_duplicates and not args.insert_new_crawl and not args.insert_new_simhashes and not args.transfer_block_lists:
        parser.print_help()
        parser.exit()

    return args

def db_connect():
    """ Establish connection to Postgres base, return a connection object """
    return pg.connect(dbname=c.database, host=c.host, port=c.port, user=c.user, password=c.password, sslmode=c.sslmode if c.sslmode else None, sslrootcert=c.sslrootcert if c.sslrootcert else None, sslcert=c.sslcert if c.sslcert else None, sslkey=c.sslkey if c.sslkey else None)

def check_if_text_in_db(con, record):
    """ Check if the fulltext is already in the db """
    with con.cursor() as cur:
        cur.execute("""SELECT fulltext_id FROM warcinfo WHERE content_hash = %s and crawl_id = %s
                  LIMIT 1;""", (record.content_hash, c.crawl_id))
        res = cur.fetchone()

        if res:
            return res[0]
        else:
            return None

def insert_fulltext(con, record):
    """ Inserts fulltext, returning id if it already exists"""
    with con.cursor() as cur:
        para = "\n".join(record.full_text)

        fulltext_sql = """WITH e AS (
                            INSERT INTO fulltext(hash,fulltext) VALUES(%s,%s) ON CONFLICT DO NOTHING RETURNING fulltext_id
                            )
                        SELECT * FROM e
                        UNION
                        SELECT fulltext_id FROM fulltext WHERE hash=%s;"""

        cur.execute(fulltext_sql, (record.full_text_hash, para, record.full_text_hash))
        fulltext_id = cur.fetchone()

        return fulltext_id

def write_warc_file(con, warc_file_name):
    """ Inserts metadata about the warc file, returning id if it already exists"""
    with con.cursor() as cur:
        warcfile_sql = """WITH e AS (
                    INSERT INTO warc_files(warc_file_name) VALUES(%s) ON CONFLICT DO NOTHING RETURNING warc_file_id
                            )
                        SELECT * FROM e
                        UNION
                        SELECT warc_file_id FROM warc_files WHERE warc_file_name=%s;"""

        cur.execute(warcfile_sql, (warc_file_name,warc_file_name))
        warc_file_id = cur.fetchone()[0]
        return warc_file_id

def write_warcinfo_record(con, record, fulltext_id):
    """ Writes the warc record to DB """ 
    with con.cursor() as cur:
        warcinfo_sql = """INSERT INTO warcinfo(crawl_id, type, record_id, concurrent_to, target_uri, date, content_hash, payload_digest, content_type, content_length, response_mime_type, response_status, redirect_location, warc_file_id, fulltext_id)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"""

        # if response, get metadata from HTTP header, if resource, assume HTML as content type and status 200
        if record.rec_headers.get("WARC-Type") == "response":
            response_mime_type = record.http_headers.get('Content-Type')
            response_status = record.http_headers.statusline
            redirect_location = record.http_headers.get('Location')
        elif record.rec_headers.get("WARC-Type") == "resource":
            response_mime_type = "text/html"
            response_status = "200 OK"
            redirect_location = None

        args = (c.crawl_id, record.rec_headers.get('WARC-Type'), record.rec_headers.get('WARC-Record-ID'), record.rec_headers.get('WARC-Concurrent-To'), record.rec_headers.get('WARC-Target-URI'), record.rec_headers.get('WARC-Date'), record.content_hash, record.rec_headers.get('WARC-Payload-Digest'), record.rec_headers.get('Content-Type'), record.rec_headers.get('Content-Length'), response_mime_type, response_status, redirect_location, record.warc_file_id, fulltext_id)

        cur.execute(warcinfo_sql, args)

def insert_new_crawl():
    """ Insert paths (= URLs within a domain) from warcinfo and deduplicate per domain"""
    with db_connect() as con:
        cur = con.cursor()
        cur.execute("CREATE TABLE paths_maalfrid_%s PARTITION OF paths FOR VALUES IN (%s);", (c.crawl_id, c.crawl_id))

        print("Inserting paths...")
        # INSERT only responses with a statuscode of 200, only crawled docs with "acutal text" (after BP removal, OCR etc.)
        cur.execute("""CREATE TEMP TABLE paths_raw(pathid SERIAL, warcinfo_running_id INT, crawl_id INT, path TEXT, domainid INT, fulltext_id INT);""")
        cur.execute("""INSERT INTO paths_raw(warcinfo_running_id, crawl_id, path, domainid, fulltext_id)
                SELECT running_id, crawl_id, regexp_replace(target_uri, '^https?\\:\\/\\/', ''), domainid, fulltext_id FROM warcinfo w
                JOIN domains d ON d.domain = reverse(split_part(reverse(substring(target_uri from '(?:.*://)?([^:/?]*)')), '.', 2)) || '.' || reverse(split_part(reverse(substring(target_uri from '(?:.*://)?([^:/?]*)')), '.', 1))
                WHERE response_status LIKE '200%%' and fulltext_id != 1 and crawl_id = %s;""", (c.crawl_id,))

        # DEDUP ON DOMAIN LEVEL
        # GROUP BY domainid and fulltext_id, select item with lowest ID
        print("Deduplicating...")
        cur.execute("""CREATE TEMP TABLE paths_dedup (pathid int);""")
        cur.execute("""INSERT INTO paths_dedup(pathid)
                    SELECT min(pathid) FROM paths_raw p
                    GROUP BY domainid,fulltext_id;""")

        # LEFT JOIN AND TAKE ONLY those not in the dedupped table
        cur.execute("""INSERT INTO paths(warcinfo_running_id, crawl_id, path, domainid, fulltext_id)
                    SELECT warcinfo_running_id, crawl_id, path, domainid, fulltext_id FROM paths_raw p
                    JOIN paths_dedup pd ON pd.pathid = p.pathid;""")

        # add content type
        print("Adding content type...")
        cur.execute("""UPDATE paths p
                    SET contenttype = 'html'
                    FROM warcinfo w
                    WHERE w.running_id = p.warcinfo_running_id and p.crawl_id = %s
                    and w.response_mime_type LIKE 'text/html%%';""", (c.crawl_id,))

        cur.execute("""UPDATE paths p
                    SET contenttype = 'pdf'
                    FROM warcinfo w
                    WHERE w.running_id = p.warcinfo_running_id and p.crawl_id = %s
                    and w.response_mime_type LIKE 'application/pdf%%';""", (c.crawl_id,))

        cur.execute("""UPDATE paths p
                    SET contenttype = 'doc'
                    FROM warcinfo w
                    WHERE w.running_id = p.warcinfo_running_id and p.crawl_id = %s
                    and (w.response_mime_type LIKE 'application/msword%%' or w.response_mime_type LIKE 'application/vnd.openxmlformats-officedocument.wordprocessingml.document%%');""", (c.crawl_id,))

        # remove dom and domFinal from path
        cur.execute("""UPDATE paths_maalfrid_%s
                    SET path = replace(path, 'urn:dom:https://', '')
                    WHERE path LIKE 'urn:dom:https://%%';""", (c.crawl_id,))
        cur.execute("""UPDATE paths_maalfrid_%s
                    SET path = replace(path, 'urn:dom:http://', '')
                    WHERE path LIKE 'urn:dom:http://%%';""", (c.crawl_id,))
        cur.execute("""UPDATE paths_maalfrid_%s
                    SET path = replace(path, 'urn:domFinal:https://', '')
                    WHERE path LIKE 'urn:domFinal:https://%%';""", (c.crawl_id,))
        cur.execute("""UPDATE paths_maalfrid_%s
                    SET path = replace(path, 'urn:domFinal:http://', '')
                    WHERE path LIKE 'urn:domFinal:http://%%';""", (c.crawl_id,))

def get_domains(con):
    """ Get a list of available domains with ids """
    with con.cursor() as cur:
        cur.execute("SELECT domainid, domain FROM domains;")
        domains = cur.fetchall()
        return domains

def check_if_empty(con, domain):
    """ Check if there are any URLS/paths in the given domain """
    with con.cursor() as cur:
        sql = """SELECT count(*) FROM paths p
                       JOIN domains d ON d.domainid = p.domainid
                       WHERE p.crawl_id = %s AND d.domain = %s;
                        """

        args = (c.crawl_id, domain)
        cur.execute(sql, args)
        return cur.fetchone()[0]

def get_sets_of_simhashes(cur, domain="nb.no", content_type="html"):
    """ Get sets of simhashes from current crawl and old crawls to compare against """

    old_sql = """ 
        CREATE TEMPORARY TABLE old AS
        SELECT p.pathid, d.domainid, p.path, p.fulltext_id, s.simhash, w.content_hash FROM paths p
        JOIN domains d ON d.domainid = p.domainid
        JOIN warcinfo w ON w.crawl_id = p.crawl_id AND w.running_id = p.warcinfo_running_id
        JOIN simhash s ON s.fulltext_id = p.fulltext_id
        WHERE p.crawl_id != %s AND d.domain = %s AND p.contenttype = %s; """

    new_sql = """ 
        CREATE TEMPORARY TABLE new AS
        SELECT p.crawl_id, p.pathid, d.domainid, p.path, p.fulltext_id, s.simhash, w.content_hash FROM paths p
        JOIN domains d ON d.domainid = p.domainid
        JOIN warcinfo w ON w.crawl_id = p.crawl_id AND w.running_id = p.warcinfo_running_id
        JOIN simhash s ON s.fulltext_id = p.fulltext_id
        WHERE p.crawl_id = %s AND d.domain = %s AND p.contenttype = %s; """

    args = (c.crawl_id, domain, content_type)

    cur.execute(old_sql, args)
    cur.execute(new_sql, args)

    cur.execute("SELECT * FROM old;")
    old = cur.fetchall()

    # add indexes for faster matching
    cur.execute("CREATE INDEX o_hash ON old(content_hash);")
    cur.execute("CREATE INDEX n_hash ON new(content_hash);")
    cur.execute("CREATE INDEX o_ft ON old(fulltext_id);")
    cur.execute("CREATE INDEX n_ft ON new(fulltext_id);")

    # reduce the candidate set by removing exact duplicates at response and fulltext level
    cur.execute("""SELECT n.* FROM new n
                   WHERE NOT EXISTS (SELECT 1 FROM old o WHERE o.content_hash = n.content_hash OR o.fulltext_id = n.fulltext_id);""")
    new = cur.fetchall()

    return old, new

def write_new_docs_to_db(con, new_docs):
    with con.cursor() as cur:
        cur.executemany("INSERT INTO new_docs_3_bits VALUES(%s,%s,%s);", new_docs)

def run_near_duplicate_detection(domain, content_type):
    with db_connect() as con:
        with con.cursor(cursor_factory=RealDictCursor) as cur:
            old, new = get_sets_of_simhashes(cur=cur, domain=domain, content_type=content_type)

    if new:
        # 10 processes and a chunksize of 500 lead to the best performance in a realistic setting
        pool = multiprocessing.Pool(c.num_parallel_processes)

        results=[]
        
        simhashes_old = serialize_simhashes(old)
        simhashes_new = serialize_simhashes(new)
        
        index = build_index(simhashes_old)

        compare_with_index = partial(compare, index)

        for i in tqdm.tqdm(pool.imap_unordered(compare_with_index, simhashes_new, chunksize=500), total=len(simhashes_new)):
            results.append(i)

        pool.close()
        pool.join()

        # flatten the list of string_ids
        fuzzy_dup = list(chain.from_iterable(results))

        # convert all ids back to integer, make a set of it
        fuzzy_dup_set = {int(x) for x in fuzzy_dup}

        new_docs = []

        # remove fuzzy duplicates
        for item in new:
            if item["fulltext_id"] in fuzzy_dup_set:
                continue
            else:
                new_docs.append((c.crawl_id, item["domainid"], item["pathid"]))

        return new_docs
    else:
        return None

def detect_near_duplicates():
    with db_connect() as con:
        domains = get_domains(con)

        # create partition
        with con.cursor() as cur:
            cur.execute("CREATE TABLE new_docs_3_bits_maalfrid_%s PARTITION OF new_docs_3_bits FOR VALUES IN (%s);", (c.crawl_id,c.crawl_id))

        for domain in domains:
            print(domain)
            count = check_if_empty(con, domain[1])

            if count > 0:
                for content_type in ['html', 'pdf', 'doc']:
                    print(content_type)
                    new_docs = run_near_duplicate_detection(domain=domain[1], content_type=content_type)

                    if new_docs:
                        with db_connect() as write_con:
                            write_new_docs_to_db(write_con, new_docs=new_docs)

def langdet_wrapper(args): 
    fulltext_id = args[0]
    text = args[1].split("\n")
    return langdet.langdet(fulltext_id, text, engine="textcat", stop_word_filter=True, apply_language_filter=True)

def simhash_wrapper(args):
    return compute_simhash(fulltext_id=args[0], doc=args[1])

def classify_documents_in_db():
    pool = multiprocessing.Pool(c.num_parallel_processes)
    results=[]
    processeditems = 0

    # fetch from DB, classify in parallel, store hash and class in memory
    with db_connect() as con:
        with con.cursor(name='fetch_result') as cur:
            # classify only non-empty documents (omit already classified docs)
            cur.execute("SELECT ft.fulltext_id, ft.fulltext FROM fulltext ft WHERE ft.hash != 'da39a3ee5e6b4b0d3255bfef95601890afd80709' AND EXISTS (SELECT 1 FROM warcinfo_maalfrid_%s w WHERE w.fulltext_id = ft.fulltext_id) ORDER BY random();", (c.crawl_id,))

            while True:
                rows = cur.fetchmany(50000)
                processeditems += 50000
                print(processeditems)
                if not rows:
                    break

                for i in pool.imap_unordered(langdet_wrapper, rows):
                    results.append(i)

    # write back to DB
    with db_connect() as con:
        with con.cursor() as cur:
            cur.execute("CREATE TABLE doclangs_maalfrid_%s PARTITION OF doclangs FOR VALUES IN (%s);", (c.crawl_id, c.crawl_id))
            for result in results:
                cur.execute("INSERT INTO doclangs(crawl_id,fulltext_id,lang,paralang,tokens,paras) VALUES(%s,%s,%s,%s,%s,%s)", (c.crawl_id, result[0], result[1], result[2], result[3], result[4]))
            con.commit()

            # aggregate paragraphs
            cur.execute("CREATE TABLE doclangs_para_maalfrid_%s PARTITION OF doclangs_para FOR VALUES IN (%s);", (c.crawl_id, c.crawl_id))
            cur.execute("""INSERT INTO doclangs_para_maalfrid_%s(crawl_id,fulltext_id,lang,tokens,paras)
                    SELECT crawl_id, fulltext_id, lang, sum(tokens), count(*)
                    FROM (SELECT d.crawl_id,
                                d.fulltext_id,
                            json_data.value->>'lang' AS lang,
                            (json_data.value->>'tokens')::int AS tokens
                    FROM doclangs_maalfrid_%s as d,
                        JSON_EACH(d.paralang) as json_data
                        WHERE --d.fulltext_id IN (
                            --  SELECT fulltext_id FROM warcinfo_fulltext wf
                            --  JOIN paths p ON p.warcinfo_running_id = wf.running_id
                                --WHERE p.contenttype IN ('html')
                            --)
                        -- omit empty lines
                        --and
                        (json_data.value->>'tokens')::int > 0
                        ) x
                    GROUP BY x.crawl_id, x.fulltext_id, x.lang;""", (c.crawl_id, c.crawl_id))

def insert_new_simhashes():
    """ Calculates simhashes for new documents """
    pool = multiprocessing.Pool(c.num_parallel_processes)
    results=[]
    processeditems = 0

    # fetch from DB, classify in parallel, store hash and class in memory
    with db_connect() as con:
        with con.cursor(name='fetch_result') as cur:
            # omit already simhashed docs
            cur.execute("SELECT ft.fulltext_id, ft.fulltext FROM fulltext ft LEFT JOIN simhash s ON s.fulltext_id = ft.fulltext_id WHERE s.fulltext_id is null and ft.hash != 'da39a3ee5e6b4b0d3255bfef95601890afd80709' ORDER BY random();")

            while True:
                rows = cur.fetchmany(50000)
                processeditems += 50000
                print(processeditems)
                if not rows:
                    break

                for i in pool.imap_unordered(simhash_wrapper, rows):
                    results.append(i)

    # write back to DB
    with db_connect() as con:
        with con.cursor() as cur:
            for result in results:
                cur.execute("INSERT INTO simhash(fulltext_id, simhash, simhash_bit) VALUES(%s,%s,%s)", (result[0], result[1], result[2]))
            con.commit()

def transfer_block_lists():
    with db_connect() as con:
        cur = con.cursor()

        # get last crawl
        cur.execute("SELECT crawl_id FROM crawls WHERE crawl_id < %s ORDER BY crawl_id DESC LIMIT 1;", (c.crawl_id,))
        old_crawl_id = cur.fetchone()[0]
        new_crawl_id = c.crawl_id

        cur.execute("SELECT entityid FROM blocked_paths_entity GROUP BY entityid ORDER BY entityid;")
        entities = cur.fetchall()

        for entity in entities:
            entityid = entity[0]
            print(entityid)

            sql = """INSERT INTO blocked_paths_entity(pathid, crawl_id, entityid)
                SELECT p2.pathid, %s, %s FROM blocked_paths_entity b 
                JOIN paths p ON p.crawl_id = b.crawl_id AND p.pathid = b.pathid
                JOIN paths p2 ON p2.crawl_id = %s and p2.path = p.path
                WHERE b.crawl_id = %s and b.entityid = %s
                ON CONFLICT DO NOTHING;"""

            cur.execute(sql, (new_crawl_id, entityid, new_crawl_id, old_crawl_id, entityid))

def process_warcs(args):
    if args.warc_file.endswith('warc.gz') and not args.warc_file.endswith('meta.warc.gz'):
        print(args.warc_file)

        # optional override of content types
        if args.content_type:
            content_types = [args.content_type]
        else:
            content_types = c.SUPPORTED_CONTENT_TYPES

        with open(args.warc_file, 'rb') as stream:
            with db_connect() as con:
                warc_file_id = write_warc_file(con, args.warc_file)
                warc_file_name = args.warc_file

                for record in wt.filter_warc(stream, content_types):
                    maalfrid_record = wt.convert_to_maalfrid_record(record, warc_file_id=warc_file_id, warc_file_name=warc_file_name, use_lenient_html_parser=args.use_lenient_html_parser, calculate_simhash=False)

                    # only insert response records with acutal content (records with parsing errors are not inserted, only logged)
                    if maalfrid_record.content != None:
                        maalfrid_record.extract_full_text()                     

                        if maalfrid_record.full_text != None:
                            try:
                                fulltext_id = insert_fulltext(con, maalfrid_record)
                            except:
                                print("WARNING: could not import full_text to database, skipping silently, but should be invesigated", args.warc_file, maalfrid_record.rec_headers.get('WARC-Record-ID'))
                                continue

                            if fulltext_id == None:
                                # sleep and retry if DB responds with None
                                # hinting at a concurrency problem
                                print("WARNING: could not fetch fulltext_id from DB (too many parallel processes?), retrying in 2 seconds", args.warc_file, maalfrid_record.rec_headers.get('WARC-Record-ID'), maalfrid_record.full_text_hash)
                                time.sleep(2)
                                fulltext_id = insert_fulltext(con, maalfrid_record)

                                if fulltext_id == None:
                                    print("WARNING: could not fetch fulltext_id from DB (too many parallel processes?), will not create simhash", args.warc_file, maalfrid_record.rec_headers.get('WARC-Record-ID'), maalfrid_record.full_text_hash)
                                    pass
                        else:
                            # if full_text could not be extracted (full_text == None), then do not import this response, jump to the next
                            continue
                            
                        write_warcinfo_record(con, maalfrid_record, fulltext_id)

                        # finally, commit the transcation
                        con.commit()
                    else:
                        # ignore responses without content
                        pass

def run(args):
    if args.warc_file:
        process_warcs(args=args)
    elif args.insert_new_crawl == True:
        insert_new_crawl()
    elif args.insert_new_simhashes == True:
        insert_new_simhashes()
    elif args.detect_near_duplicates == True:
        detect_near_duplicates()
    elif args.classify == True:
        classify_documents_in_db()
    elif args.transfer_block_lists == True:
        transfer_block_lists()
    

if __name__ == '__main__':
    args = parse_args()
    run(args)
