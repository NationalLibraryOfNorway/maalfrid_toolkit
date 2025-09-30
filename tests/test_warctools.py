import os

import pytest

import maalfrid_toolkit.warc_tools as warc_tools

test_file_path = os.path.join(os.path.dirname(__file__), "testfiles")


@pytest.fixture
def load_html_warc():
    with open(os.path.join(test_file_path, "html.warc.gz"), "rb") as stream:
        yield stream


@pytest.fixture
def load_pdf_warc():
    with open(os.path.join(test_file_path, "pdf.warc.gz"), "rb") as stream:
        yield stream


@pytest.fixture
def load_docx_warc():
    with open(os.path.join(test_file_path, "docx.warc.gz"), "rb") as stream:
        yield stream


def test_warc_filter(load_html_warc):
    records = [
        record
        for record in warc_tools.filter_warc(
            load_html_warc, content_types=["text/html"]
        )
    ]
    assert len(records) == 1


def test_maalfrid_record_init(load_html_warc):
    for record in warc_tools.filter_warc(load_html_warc, content_types=["text/html"]):
        maalfrid_record = warc_tools.convert_to_maalfrid_record(
            record, warc_file_name="testfiles/html.warc.gz"
        )
        assert maalfrid_record.content_type.startswith("text/html")


def test_maalfrid_record_ft_extract_html(load_html_warc):
    for record in warc_tools.filter_warc(load_html_warc, content_types=["text/html"]):
        maalfrid_record = warc_tools.convert_to_maalfrid_record(
            record, warc_file_name="testfiles/html.warc.gz"
        )
        maalfrid_record.extract_full_text()
        assert maalfrid_record.full_text[2].startswith("Dataa vart samla inn") == True


def test_maalfrid_record_ft_extract_pdf(load_pdf_warc):
    for record in warc_tools.filter_warc(
        load_pdf_warc, content_types=["application/pdf"]
    ):
        maalfrid_record = warc_tools.convert_to_maalfrid_record(
            record, warc_file_name="testfiles/pdf.warc.gz"
        )
        maalfrid_record.extract_full_text()
        assert maalfrid_record.full_text[2].startswith("The corpus") == True


def test_maalfrid_record_ft_extract_doc(load_docx_warc):
    for record in warc_tools.filter_warc(
        load_docx_warc,
        content_types=[
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ],
    ):
        maalfrid_record = warc_tools.convert_to_maalfrid_record(
            record, warc_file_name="testfiles/docx.warc.gz"
        )
        maalfrid_record.extract_full_text()
        assert maalfrid_record.full_text[2].startswith("(2019–2020)") == True


def test_maalfrid_record_get_simhash(load_html_warc):
    for record in warc_tools.filter_warc(load_html_warc, content_types=["text/html"]):
        maalfrid_record = warc_tools.convert_to_maalfrid_record(
            record, warc_file_name="testfiles/html.warc.gz", calculate_simhash=True
        )
        maalfrid_record.extract_full_text()
        assert maalfrid_record.simhash_value == 11772415046536287686


def test_maalfrid_record_get_metadata(load_html_warc):
    for record in warc_tools.filter_warc(load_html_warc, content_types=["text/html"]):
        maalfrid_record = warc_tools.convert_to_maalfrid_record(
            record, warc_file_name="testfiles/html.warc.gz", calculate_simhash=True
        )
        maalfrid_record.extract_full_text()
        maalfrid_record.extract_metadata()
        assert maalfrid_record.metadata == {'viewport': 'width=device-width, initial-scale=1', 'robots': 'index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1', 'og:locale': 'nb_NO', 'og:locale:alternate': 'en_GB', 'og:type': 'article', 'og:title': 'Målfrid 2024 – Fritt tilgjengelege tekster frå norske statlege nettsider', 'og:url': 'https://www.nb.no/sprakbanken/ressurskatalog/oai-nb-no-sbr-99/', 'og:site_name': 'Språkbanken', 'article:modified_time': '2025-02-10T09:56:15+00:00', 'twitter:card': 'summary_large_image', 'twitter:label1': 'Ansl. lesetid', 'twitter:data1': '3 minutter', 'generator': 'WordPress 6.7.2', 'msapplication-TileImage': 'https://www.nb.no/content/uploads/sites/16/2020/05/nb-logo.png'}


def test_maalfrid_record_get_title(load_html_warc):
    for record in warc_tools.filter_warc(load_html_warc, content_types=["text/html"]):
        maalfrid_record = warc_tools.convert_to_maalfrid_record(
            record, warc_file_name="testfiles/html.warc.gz", calculate_simhash=True
        )
        maalfrid_record.extract_full_text()
        maalfrid_record.extract_metadata()
        assert (
            maalfrid_record.title
            == "Målfrid 2024 – Fritt tilgjengelege tekster frå norske statlege nettsider - Språkbanken"
        )

def test_maalfrid_record_estimate_date(load_html_warc):
    for record in warc_tools.filter_warc(load_html_warc, content_types=["text/html"]):
        maalfrid_record = warc_tools.convert_to_maalfrid_record(
            record, warc_file_name="testfiles/html.warc.gz", calculate_simhash=True
        )
        maalfrid_record.extract_full_text()
        maalfrid_record.extract_metadata()
        maalfrid_record.estimate_date()
        assert (
            maalfrid_record.estimated_date
            == "2025-02-10"
        )
