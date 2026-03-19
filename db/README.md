# Database (PostgreSQL)

## First steps

If you want to process and inspect the crawled dataset in a DB, you can use the following setup (the example uses PostgreSQL):

```bash
psql -c "CREATE DATABASE maalfrid_test"
psql -d maalfrid_test -f schema.sql
psql -d maalfrid_test -f indices.sql
```

You need to import the domains that you want to process to the __domains__ table prior to import, e.g.:

```sql
INSERT INTO domains(domain) VALUES('example.com');
```

Remember to set up the .env file in the project root folder accordingly (an example can be found in env-example).

# Full pipeline: Database ingestion

Prior to running this, remember to set correct crawl_id in _config.py_ and create a warcinfo_partition for that crawl.

## Extract data from WARC files and insert to DB

```bash
find -name "*.warc.gz" | shuf | parallel -u -j5 "pdm run python3 -m maalfrid_toolkit.db --mode precision --extract_metadata --warc_file {}"
```

## Run language identification on new documents

```bash
pdm run python3 -m maalfrid_toolkit.db --classify
```

## Extract relevant WARC records and do content_type normalization

```bash
pdm run python3 -m maalfrid_toolkit.db --insert_new_crawl
```

## Transfer URL block lists from last crawl

```bash
pdm run python3 -m maalfrid_toolkit.db --transfer_block_lists
```

## Calculate simhashes for new documents (only relevant if you have more than one crawl)

```bash
pdm run python3 -m maalfrid_toolkit.db --insert_new_simhashes
```

## Detect new documents since last crawls using the simhashes (only relevant if you have more than one crawl)

```bash
pdm run python3 -m maalfrid_toolkit.db --detect_near_duplicates
```

