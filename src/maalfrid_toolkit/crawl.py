import sys
import shutil
import os
import subprocess
from datetime import datetime
import maalfrid_toolkit.config as c
import yaml
import uuid
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re

# create start timestamp
timestamp = datetime.now()
timestamp_string = datetime.strftime(timestamp, format='%Y%m%d_%H%M%S')

# create unique event id
instance_id = str(uuid.uuid4())

def create_folders(prefix):
    # check if output folder exists, if not, create it
    path_to_output_folder = os.path.join(c.current_dir, "warc", prefix)
    if not os.path.exists(path_to_output_folder):
        os.makedirs(path_to_output_folder)

    # check if log folder exists, if not, create it
    path_to_logs_folder = os.path.join(c.current_dir, "logs", prefix)
    if not os.path.exists(path_to_logs_folder):
        os.makedirs(path_to_logs_folder)

    # check if finished folder exists, if not, create it
    path_to_finished_folder = os.path.join(path_to_output_folder, 'finished')
    if not os.path.exists(path_to_finished_folder):
        os.makedirs(path_to_finished_folder)

    return path_to_output_folder, path_to_logs_folder, path_to_finished_folder

## SITEMAP CRAWLER
def request(myURL):
    headers = {
        'User-Agent': c.user_agent
    }

    page = requests.get(myURL, headers=headers)
    return page

def extract_urls(page):
    soup = BeautifulSoup(page.content, 'xml')
    urls = soup.find_all('loc', recursive=True)

    for url in urls:
        parsed_url = urlparse(url.text)
        parsed_url = parsed_url.path 

        if re.search(r'sitemap|\.xml/?$', parsed_url):
            yield from(extract_urls(request(url.text)))
        else:
            yield(url.text)

    time.sleep(2)

def sitemap_crawler(myURL):
    urls = []

    for url in extract_urls(request(myURL)):
        urls.append(url)

    # deduplicate URL list
    urls = list(set(urls))
    # sort it
    urls.sort()

    return urls

## WGET CRAWLER

def parse_configuration(crawljob_config_path):
    with open(crawljob_config_path, 'r') as file:
        crawljob_config = yaml.safe_load(file)
        return crawljob_config

def get_collection_name(prefix, domain_name):
    # WARC FILENAME ACCORDING TO IIPC RECCOMANDATION: prefix-timestamp-serial-crawlhost.warc.gz
    # SERIAL = instance_id
    domain_name = domain_name.replace('.', '_')[:30]
    collection_name = '%s-%s-%s-%s' % (prefix, timestamp_string, instance_id, domain_name)
    return collection_name

def run_browsertrix(crawljob_config):
    # first check if the crawljob is enabled
    if crawljob_config["enabled"] == False:
        print("Crawljob %s for %s is disabled, exiting." % (crawljob_config["jobid"], crawljob_config["domain"]))
        sys.exit(1)

    if crawljob_config["exclude_subdomains"] != [None]:
        exclude_subdomains_clause = '--exclude ' + ' --exclude '.join(crawljob_config["exclude_subdomains"])
    else:
        exclude_subdomains_clause = ''

    if crawljob_config["exclude_paths"] != [None]:
        exclude_paths_clause = '--exclude ' + ' --exclude '.join(crawljob_config["exclude_paths"])
    else:
        exclude_paths_clause = ''

    if crawljob_config["exclude_urls"] != [None]:
        exclude_urls_clause = '--exclude ' + ' --exclude '.join(crawljob_config["exclude_urls"])
    else:
        exclude_urls_clause = ''

    if crawljob_config["use_sitemap"] == True:
        sitemap_clause = "--sitemap"
    else:
        sitemap_clause = ""

    prefix = c.prefix + "_browsertrix"
    collection_name = get_collection_name(prefix=prefix, domain_name=crawljob_config["domain"])

    path_to_output_folder, path_to_logs_folder, path_to_finished_folder = create_folders(prefix)

    try:
        command = f"""docker run -v {path_to_output_folder}:/crawls maalfrid-browsertrix crawl --url {crawljob_config["seed"]} --combineWARC --generateCDX --saveState --waitUntil networkidle0 --behaviors autoscroll,autofetch,siteSpecific --postLoadDelay 2 --userAgent "{c.user_agent}" --scopeType domain --text to-warc --text final-to-warc --dom to-warc --dom final-to-warc --delay 2 --workers 1 --timeLimit {crawljob_config["timeout_seconds"]} {exclude_subdomains_clause} {exclude_paths_clause} {exclude_urls_clause} {sitemap_clause} --collection {collection_name}"""

        # write log entry
        event_start_log = {"instance_id": instance_id, "crawler": "browsertrix", "jobid": crawljob_config["jobid"], "domain": crawljob_config["domain"], "event": "start", "timestamp": timestamp_string, "args": command}
        with open('%s/%s.jsonl' % (path_to_logs_folder, collection_name), 'a') as f:
            f.write(json.dumps(event_start_log) + "\n")

        print("Crawling", crawljob_config["domain"], "with ID:", instance_id)
        p = subprocess.run(command, shell=True, capture_output=True)

        if p.returncode == 0:
            print("domain %s: SUCCESS, returned: %s" % (crawljob_config["domain"], str(p.stdout)))
        elif p.returncode <= 125:
            print("domain %s: FAIL, exit-code=%d error = %s" % (crawljob_config["domain"], p.returncode, str(p.stderr)))
    except:
        print("an unknown problem occured when downloading", crawljob_config["domain"])
    finally:
        timestamp_end = datetime.now()
        timestamp_end_string = datetime.strftime(timestamp_end, format='%Y%m%d_%H%M%S')

        # try to get statuscode
        if 'status_code' in locals():
            pass
        else:
            try:
                status_code = str(p.returncode)
            except:
                status_code = 'abnormal exit'

        event_end_log = {"instance_id": instance_id, "crawler": "browsertrix", "jobid": crawljob_config["jobid"], "domain": crawljob_config["domain"], "event": "end", "status_code": status_code, "timestamp": timestamp_end_string}

        # write to log
        with open('%s/%s.jsonl' % (path_to_logs_folder, collection_name), 'a') as f:
            f.write(json.dumps(event_end_log) + "\n")

        # find files in browsertrix folder
        path_to_browsertrix_folder = os.path.join(path_to_output_folder, 'collections', collection_name)

        files = os.listdir(path_to_browsertrix_folder)

        for file in files:
            path_to_warc_file = os.path.join(path_to_browsertrix_folder, file)
            if file.startswith(collection_name):
                shutil.move(path_to_warc_file, path_to_finished_folder)


def run_wget(crawljob_config):
    # first check if the crawljob is enabled
    if crawljob_config["enabled"] == False:
        print("Crawljob %s for %s is disabled, exiting." % (crawljob_config["jobid"], crawljob_config["domain"]))
        sys.exit(1)

    try:
        timeout_seconds = int(crawljob_config["timeout_seconds"])
    except:
        timeout_seconds = None

    prefix = c.prefix + "_wget"
    warc_filename = get_collection_name(prefix=prefix, domain_name=crawljob_config["domain"])

    path_to_output_folder, path_to_logs_folder, path_to_finished_folder = create_folders(prefix)

    if crawljob_config["span_hosts"] == True:
        span_hosts_clause = '-H'
    else:
        span_hosts_clause = ''

    if crawljob_config["ignore_robotstxt"] == True:
        robotstxt_clause = "-e robots=off"
    else:
        robotstxt_clause = ""

    if crawljob_config["exclude_subdomains"] != [None]:
        exclude_subdomains_clause = '--exclude-domains=%s' % (','.join(crawljob_config["exclude_subdomains"]))
    else:
        exclude_subdomains_clause = ''

    if crawljob_config["exclude_paths"] != [None]:
        exclude_paths_clause = '--exclude-directories=%s' % (','.join(crawljob_config["exclude_paths"]))
    else:
        exclude_paths_clause = ''

    if crawljob_config["exclude_urls"] != [None]:
        exclude_urls_clause = '--reject-regex=%s' % ('|'.join(crawljob_config["exclude_urls"]))
    else:
        exclude_urls_clause = ''

    path_to_crawljobs_folder = os.path.join(c.current_dir, "crawljobs")

    # initiate wget using subprocess
    try:
        args = ['wget', '--config=%s/wget_warc.conf' % (path_to_crawljobs_folder), '--level=%s' % (crawljob_config["crawl_depth"]), *([span_hosts_clause] if span_hosts_clause else []), *([robotstxt_clause] if robotstxt_clause else []), '-P%s/tempstore' % (path_to_output_folder), '-D%s' % (crawljob_config["domain"]), *([exclude_subdomains_clause] if exclude_subdomains_clause else []), *([exclude_paths_clause] if exclude_paths_clause else []), *([exclude_urls_clause] if exclude_urls_clause else []), '--warc-file=%s/%s' % (path_to_output_folder, warc_filename), crawljob_config["seed"]]

        # write log entry
        event_start_log = {"instance_id": instance_id, "crawler": "wget", "jobid": crawljob_config["jobid"], "domain": crawljob_config["domain"], "event": "start", "timestamp": timestamp_string, "args": ' '.join(args)}
        with open('%s/%s.jsonl' % (path_to_logs_folder, warc_filename), 'a') as f:
            f.write(json.dumps(event_start_log) + "\n")

        print("Crawling", crawljob_config["domain"], "with ID:", instance_id)
        p = subprocess.run(args, capture_output=True, timeout=timeout_seconds)

        if p.returncode == 0:
            print("domain %s: SUCCESS, returned: %s" % (crawljob_config["domain"], str(p.stdout)))
        elif p.returncode <= 125:
            print("domain %s: FAIL, exit-code=%d error = %s" % (crawljob_config["domain"], p.returncode, str(p.stderr)))
    except subprocess.TimeoutExpired:
        print("timeout of", str(timeout_seconds), "expired on domain", crawljob_config["domain"])
        status_code = "-15"
    except:
        print("an unknown problem occured when downloading", crawljob_config["domain"])
    finally:
        timestamp_end = datetime.now()
        timestamp_end_string = datetime.strftime(timestamp_end, format='%Y%m%d_%H%M%S')

        # try to get statuscode
        if 'status_code' in locals():
            pass
        else:
            try:
                status_code = str(p.returncode)
            except:
                status_code = 'abnormal exit'

        event_end_log = {"instance_id": instance_id, "crawler": "wget", "jobid": crawljob_config["jobid"], "domain": crawljob_config["domain"], "event": "end", "status_code": status_code, "timestamp": timestamp_end_string}

        # write to log
        with open('%s/%s.jsonl' % (path_to_logs_folder, warc_filename), 'a') as f:
            f.write(json.dumps(event_end_log) + "\n")

        # find files
        wget_files = os.listdir(path_to_output_folder)

        for wget_file in wget_files:
            path_to_wget_file = os.path.join(path_to_output_folder, wget_file)
            if wget_file.startswith(warc_filename):
                shutil.move(path_to_wget_file, path_to_finished_folder)

def run():
    # take configuration from argument
    crawljob_config_path = sys.argv[1]

    # parse config
    crawljob_config = parse_configuration(crawljob_config_path)

    if crawljob_config:
        try:
            crawler = crawljob_config["crawler"]
        except:
            crawler = "wget"

        if crawler == "wget":
            run_wget(crawljob_config)
        elif crawler == "browsertrix":
            run_browsertrix(crawljob_config)

if __name__ == '__main__':
    run()
