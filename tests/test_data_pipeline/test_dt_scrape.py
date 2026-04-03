import json
import runpy
import time
from pathlib import Path

import pytest

from conftest import FakeElement, install_fake_selenium


pytestmark = pytest.mark.scrape


class FakeArticle:
    def __init__(self, title, description, link):
        self.title = title
        self.description = description
        self.link = link

    def find_elements(self, by, selector):
        if selector == "h3.article-title":
            return [FakeElement(text=self.title)] if self.title is not None else []
        return []

    def find_element(self, by, selector):
        if selector == 'a[data-prop="sapo"]':
            return FakeElement(text=self.description, attrs={"href": self.link})
        raise ValueError(selector)


class FakeDTDriver:
    def __init__(self, with_noise=False, missing_meta=False):
        self.current_url = ""
        self.with_noise = with_noise
        self.missing_meta = missing_meta

    def get(self, url):
        self.current_url = url

    def quit(self):
        return None

    def find_element(self, by, selector):
        if selector == "a[aria-label]":
            return FakeElement(attrs={"aria-label": "Dân Trí"})
        raise ValueError(selector)

    def find_elements(self, by, selector):
        if selector == "div.article-content":
            if self.with_noise:
                return [
                    FakeArticle("Tin A", "Mo ta A", "https://dantri.vn/a"),
                    FakeArticle(None, "Mo ta khong tieu de", "https://dantri.vn/no-title"),
                    FakeArticle("Tin B", "Mo ta B", ""),
                    FakeArticle("Tin C", "Mo ta C", "https://dantri.vn/eclick-ads"),
                    FakeArticle("Tin A", "Mo ta A", "https://dantri.vn/a"),
                ]
            return [
                FakeArticle("Tin A", "Mo ta A", "https://dantri.vn/a"),
                FakeArticle("Tin B", "Mo ta B", "https://dantri.vn/b"),
            ]
        if selector == "time[datetime]":
            if self.missing_meta and self.current_url.endswith("/no-title"):
                return []
            return [FakeElement(text="Thứ sáu, 06/03/2026 - 15:58")]
        return []


def test_dt_scrape_end_to_end_basic_output(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[2]
    script = root / "src" / "data-pipeline" / "scrape_from_DT.py"

    driver = FakeDTDriver(with_noise=False)
    install_fake_selenium(monkeypatch, driver)

    monkeypatch.setattr(time, "sleep", lambda *_: None)
    monkeypatch.chdir(tmp_path)

    runpy.run_path(str(script), run_name="__main__")

    output_path = tmp_path / "raw_data" / "raw_data_DT.json"
    assert output_path.exists()

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["source_platform"] == "Dân Trí"
    assert len(data["post_detail"]) == 2
    assert all("title" in p and "description" in p and "created_at" in p for p in data["post_detail"])


def test_dt_scrape_noise_and_missing_metadata_scenario(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[2]
    script = root / "src" / "data-pipeline" / "scrape_from_DT.py"

    driver = FakeDTDriver(with_noise=True, missing_meta=True)
    install_fake_selenium(monkeypatch, driver)

    monkeypatch.setattr(time, "sleep", lambda *_: None)
    monkeypatch.chdir(tmp_path)

    runpy.run_path(str(script), run_name="__main__")

    output_path = tmp_path / "raw_data" / "raw_data_DT.json"
    data = json.loads(output_path.read_text(encoding="utf-8"))

    assert len(data["post_detail"]) == 2
    titles = [item["title"] for item in data["post_detail"]]
    assert "Tin A" in titles
    assert "" in titles

    missing_meta_post = next(item for item in data["post_detail"] if item["title"] == "")
    assert missing_meta_post["created_at"] == ""
