# Maalfrid toolkit

__maalfrid_toolkit__ is a Python package designed for crawling and extracting natural language data from documents found on the web (HTML, PDF, DOC). It is primarily used in the Målfrid project, a collaboration between the National Library of Norway and The Language Council of Norway, which aims to measure the usage of the two official Norwegian language forms, Bokmål and Nynorsk, on Norwegian public sector websites. While the toolkit has a particular emphasis on the Nordic countries, it supports extraction and language detection of more than 60 languages.

It builds upon:
- [wget](https://www.gnu.org/software/wget/) and [(custom) browsertrix](https://github.com/Sprakbanken/browsertrix-crawler/) for crawling
- [JusText](https://github.com/miso-belica/jusText) for HTML boilerplate removal
- [Notram PDF text extraction](https://github.com/NbAiLab/notram/) from NB AI-lab
- DOC extraction using docx2txt and antiword
- [Gielladetect/pytextcat](https://github.com/NationalLibraryOfNorway/gielladetect) and [GlotLID V3](https://huggingface.co/cis-lmu/glotlid) for language detection
- [Simhash](https://github.com/1e0ng/simhash) for near-duplicate detection

# Install
## Install with pip

```bash
pip install maalfrid_toolkit
```

With Glotlid / fasttext (optional, see below for caveats):

```bash
pip install maalfrid_toolkit[glotlid]
```

## Install with pdm

```bash
pdm install
```

## Test run pipeline

### On HTML

```bash
python -m maalfrid_toolkit.pipeline --url https://www.nb.no/utstilling/opplyst-glimt-fra-en-kulturhistorie/ --to_jsonl
```

### On PDF

```bash
python -m maalfrid_toolkit.pipeline --url https://www.nb.no/sbfil/dok/nst_taledat_dk.pdf --to_jsonl
```

### On DOC

```bash
python -m maalfrid_toolkit.pipeline --url https://www.nb.no/content/uploads/2018/11/Søknadsskjema-Bokhylla-2.doc --to_jsonl
```

### On WARC file (e.g. from self-crawled material)

```bash
python -m maalfrid_toolkit.pipeline --warc_file example_com-00000.warc.gz --calculate_simhash --to_jsonl > warc.jsonl
```

### On sitemap

```bash
python -m maalfrid_toolkit.pipeline --url https://example.com/sitemap.xml --crawl_sitemap --to_jsonl > example.jsonl
```

## Database (Postgres)

If you want to store and process the data further in a database, setup a Postgres database and enter your credentials in an .env file in the package root directory (see env-example). Be sure to populate the database with schema and indices found in db/ prior to running the commands in maalfrid_toolkit.db.

## OS-level dependencies (tested with Ubuntu 24.04) for optional functionality

### For fasttext (optional)

```bash
sudo apt-get install build-essential python3-dev
```

### For .doc text extraction (optional)

```bash
sudo apt-get install antiword
```

## A note on using Browsertrix

In order to use Browsertrix for crawling JavaScript-heavy pages and extract text from HTML, you must currently clone a custom Browsertrix from:

https://github.com/Sprakbanken/browsertrix-crawler/tree/add-dom-resource

Then build with Docker:

```bash
docker build -t maalfrid-browsertrix .
```

## License
GPL
