from pathlib import Path

import pytest

from maalfrid_toolkit import config
from maalfrid_toolkit.crawl import run_wget
from src.maalfrid_toolkit.warc_tools import convert_to_maalfrid_record, filter_warc


@pytest.fixture
def temp_test_dir(tmp_path_factory):
    yield tmp_path_factory.mktemp(basename="maalfrid_toolkit-crawl")


@pytest.fixture
def crawl_config_dhnbno():
    yield {
        "jobid": 1,
        "domain": "dh.nb.no",
        "crawler": "wget",
        "seed": "https://dh.nb.no",
        "span_hosts": True,
        "crawl_depth": 12,
        "enabled": True,
        "timeout_seconds": 1209600,
        "exclude_paths": [],
        "exclude_subdomains": [],
        "exclude_urls": [],
        "use_sitemap": False,
        "ignore_robotstxt": False,
    }


def test_pipeline(temp_test_dir, crawl_config_dhnbno):
    config.output_dir = temp_test_dir
    run_wget(crawl_config_dhnbno)

    paths = [
        path
        for path in Path(temp_test_dir)
        .joinpath("warc", "test-prefix_wget", "finished")
        .glob("*.warc.gz")
        if "meta" not in path.stem
    ]
    assert len(paths) == 1
    path = paths[0]
    with open(path, "rb") as stream:
        records = [
            convert_to_maalfrid_record(record, warc_file_name=path)
            for record in filter_warc(stream)
        ]
        assert len(records) == 1
        record = records[0]
        record.extract_full_text()
        assert record.title == "DH-LAB | Nasjonalbiblioteket"
        assert record.metadata == {
            "viewport": "width=device-width, initial-scale=1",
            "robots": "index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1",
            "twitter:card": "summary_large_image",
            "twitter:label1": "Ansl. lesetid",
            "twitter:data1": "1 minutt",
            "msapplication-TileImage": "https://www.nb.no/content/uploads/2024/01/cropped-Nasjonalbiblioteket-—-Logo-—-Bla-—-Hvit-bakgrunn-270x270.png",
        }
