import json
import runpy
import time
from pathlib import Path

import pytest

from conftest import FakeElement, install_fake_selenium


pytestmark = pytest.mark.scrape


class FakeVNArticle:
    def __init__(self, title, description, link):
        self.title = title
        self.description = description
        self.link = link

    def find_elements(self, by, selector):
        if selector in ("h3.title-news, h4.title-news",):
            return [FakeElement(text=self.title)] if self.title is not None else []
        if selector == "p.description":
            return [FakeElement(text=self.description)]
        if selector == "h3.title-news a, h4.title-news a":
            return [FakeElement(attrs={"href": self.link})]
        return []


class FakeVNEPDriver:
    def __init__(self, with_noise=False, missing_meta=False):
        self.current_url = ""
        self.with_noise = with_noise
        self.missing_meta = missing_meta

    def get(self, url):
        self.current_url = url

    def quit(self):
        return None

    def find_element(self, by, selector):
        if selector == "a.logo":
            return FakeElement(attrs={"title": "VnExpress"})
        raise ValueError(selector)

    def find_elements(self, by, selector):
        if selector == "article.item-news.item-news-common.thumb-left:not(.hidden)":
            if self.with_noise:
                return [
                    FakeVNArticle("Bai 1", "Mo ta 1", "https://vnexpress.net/1"),
                    FakeVNArticle(None, "Mo ta no title", "https://vnexpress.net/no-title"),
                    FakeVNArticle("Bai 2", "Mo ta 2", ""),
                    FakeVNArticle("Bai 3", "Mo ta 3", "https://vnexpress.net/eclick-ad"),
                    FakeVNArticle("Bai 1", "Mo ta 1", "https://vnexpress.net/1"),
                ]
            return [
                FakeVNArticle("Bai 1", "Mo ta 1", "https://vnexpress.net/1"),
                FakeVNArticle("Bai 2", "Mo ta 2", "https://vnexpress.net/2"),
            ]
        if selector == "span.date":
            if self.missing_meta and self.current_url.endswith("/no-title"):
                return []
            return [FakeElement(text="Thứ sáu, 6/3/2026, 07:00 (GMT+7)")]
        return []


def test_vn_express_scrape_end_to_end_basic_output(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[2]
    script = root / "src" / "data-pipeline" / "scrape_from_VN-EP.py"

    driver = FakeVNEPDriver(with_noise=False)
    install_fake_selenium(monkeypatch, driver)

    monkeypatch.setattr(time, "sleep", lambda *_: None)
    monkeypatch.chdir(tmp_path)

    runpy.run_path(str(script), run_name="__main__")

    output_path = tmp_path / "raw_data" / "raw_data_VN-EP.json"
    assert output_path.exists()

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["source_platform"] == "VnExpress"
    assert len(data["post_detail"]) == 2
    assert all("title" in p and "description" in p and "created_at" in p for p in data["post_detail"])


def test_vn_express_scrape_noise_and_missing_metadata_scenario(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[2]
    script = root / "src" / "data-pipeline" / "scrape_from_VN-EP.py"

    driver = FakeVNEPDriver(with_noise=True, missing_meta=True)
    install_fake_selenium(monkeypatch, driver)

    monkeypatch.setattr(time, "sleep", lambda *_: None)
    monkeypatch.chdir(tmp_path)

    runpy.run_path(str(script), run_name="__main__")

    output_path = tmp_path / "raw_data" / "raw_data_VN-EP.json"
    data = json.loads(output_path.read_text(encoding="utf-8"))

    assert len(data["post_detail"]) == 2
    titles = [item["title"] for item in data["post_detail"]]
    assert "Bai 1" in titles
    assert "" in titles

    missing_meta_post = next(item for item in data["post_detail"] if item["title"] == "")
    assert missing_meta_post["created_at"] == ""
