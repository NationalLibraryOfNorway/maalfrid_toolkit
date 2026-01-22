-- ENTITY/DOMAIN MODEL

CREATE TABLE domains (domainid SERIAL PRIMARY KEY, domain text UNIQUE);
CREATE TABLE entities ("entityID" INT PRIMARY KEY, "entityName" text, "entityNameAlt" text, "organizationNumber" numeric, deleted bool, deletion_date text, enhetsregisteret_blob json, homepage text, comment text, creation_date text, "mainDomain" integer references domains, pliktgruppe integer, dep text);
CREAtE TABLE domain_entity (domain_entity_id SERIAL PRIMARY KEY, entityid INT REFERENCES entities("entityID") ON UPDATE CASCADE ON DELETE CASCADE, domainid INT REFERENCES domains(domainid) ON DELETE CASCADE ON UPDATE CASCADE);
-- ALLOW ONLY unqiue pairs of entities and domains
ALTER TABLE domain_entity ADD CONSTRAINT entityid_domainid UNIQUE(entityid,domainid);

-- CRAWL PART

CREATE TABLE crawls (crawl_id INT PRIMARY KEY, name TEXT NOT NULL UNIQUE, year INT, comment TEXT);
CREATE TABLE warc_files(warc_file_id SERIAL PRIMARY KEY, warc_file_name text UNIQUE);

-- FULLTEXT

CREATE TABLE fulltext (fulltext_id SERIAL PRIMARY KEY, hash text UNIQUE NOT NULL, fulltext text);
CREATE TABLE simhash (fulltext_id INT PRIMARY KEY REFERENCES fulltext(fulltext_id) ON UPDATE CASCADE ON DELETE CASCADE, simhash numeric, simhash_bit bit(64));

-- WARCINFO
CREATE TABLE warcinfo(running_id SERIAL, crawl_id INT, type text, record_id text, concurrent_to text, target_uri text, date text, estimated_date text, title text, extracted_metadata jsonb, content_hash text, payload_digest text, content_type text, content_length bigint, response_mime_type text, response_status text, redirect_location text, warc_file_id int REFERENCES warc_files(warc_file_id), fulltext_id integer REFERENCES fulltext(fulltext_id)) PARTITION BY LIST(crawl_id);

-- CREATE PARTITIONS
CREATE TABLE warcinfo_maalfrid_1 PARTITION OF warcinfo FOR VALUES IN (1);
ALTER TABLE warcinfo ADD CONSTRAINT warcinfo_record_id_key UNIQUE(record_id,crawl_id);
ALTER TABLE warcinfo ADD CONSTRAINT running_id_crawl_id PRIMARY KEY(running_id,crawl_id);

--CREATE TABLE warc_domain(warc_domain_id SERIAL PRIMARY KEY, warc_file_id INT REFERENCES warc_files(warc_file_id) ON UPDATE CASCADE ON DELETE CASCADE, domain text, topdomain text);
CREATE TABLE doclangs (doclang_id SERIAL, crawl_id INT, fulltext_id int, lang text, paralang json, tokens int, paras int, PRIMARY KEY(doclang_id, crawl_id)) PARTITION BY LIST(crawl_id);
CREATE TABLE doclangs_para (doclang_para_id SERIAL, crawl_id INT, fulltext_id int REFERENCES fulltext(fulltext_id) ON UPDATE CASCADE ON DELETE CASCADE, lang text, tokens int, paras int, PRIMARY KEY (doclang_para_id, crawl_id)) PARTITION BY LIST(crawl_id);

CREATE TABLE paths (pathid SERIAL, crawl_id INT, warcinfo_running_id INT, path text, surt text, contenttype varchar(4), domainid int REFERENCES domains(domainid), fulltext_id integer REFERENCES fulltext(fulltext_id), PRIMARY KEY (pathid,crawl_id)) PARTITION BY LIST(crawl_id);
ALTER TABLE paths ADD CONSTRAINT paths_running_id FOREIGN KEY(warcinfo_running_id,crawl_id) REFERENCES warcinfo(running_id,crawl_id) ON UPDATE CASCADE ON DELETE CASCADE;

--CREATE TABLE paths_domain (pathid int, full_domain text, domain text);
CREATE TABLE blocked_paths_entity (blocked_path_entity_id SERIAL PRIMARY KEY, pathid int, crawl_id int, entityid INT REFERENCES entities("entityID") ON UPDATE CASCADE ON DELETE CASCADE);
ALTER TABLE blocked_paths_entity ADD CONSTRAINT bpe_pathid_crawlid FOREIGN KEY(pathid, crawl_id) REFERENCES paths(pathid, crawl_id) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE blocked_paths_entity ADD CONSTRAINT pathid_entityid UNIQUE(pathid,entityid);

-- NEW DOCS
CREATE TABLE public.new_docs_3_bits (
    crawl_id numeric NULL,
    domainid numeric NULL,
    pathid numeric NULL
)
PARTITION BY LIST (crawl_id);

