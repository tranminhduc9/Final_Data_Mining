import json
import runpy
import time
from pathlib import Path

import pytest

from conftest import FakeElement, install_fake_selenium


pytestmark = pytest.mark.scrape


class _FakeParagraphContainer:
    def __init__(self, texts):
        self.texts = texts

    def find_elements(self, by, selector):
        if selector == "p" or selector == "p.Normal":
            return [FakeElement(text=t) for t in self.texts]
        return []


class FakeGenKArticle:
    def __init__(self, title, href):
        self.title = title
        self.href = href

    def find_elements(self, by, selector):
        if selector == "h4.knswli-title a":
            return [FakeElement(attrs={"href": self.href})] if self.href is not None else []
        if selector == "h4.knswli-title":
            return [FakeElement(text=self.title)] if self.title is not None else []
        return []


class FakeGenKDriver:
    def __init__(self, no_such_exc):
        self.no_such_exc = no_such_exc
        self.current_url = ""

    def get(self, url):
        self.current_url = url

    def quit(self):
        return None

    def execute_script(self, script, *args):
        if "return Math.max" in script:
            return 2000
        return None

    def find_element(self, by, selector):
        if (
            by == "id"
            and selector == "ContentDetail"
            and self.current_url.startswith("https://genk.vn/article-")
        ):
            return _FakeParagraphContainer(["Noi dung 1", "Noi dung 2"])
        raise self.no_such_exc(selector)

    def find_elements(self, by, selector):
        if selector == "a.btnviewmore":
            return [FakeElement(text="Xem thêm")]
        if selector == "div.elp-list":
            return [
                FakeGenKArticle("Bai AI 1", "https://genk.vn/article-1"),
                FakeGenKArticle("Bai AI 2", "https://genk.vn/article-2"),
                FakeGenKArticle("Bai Loi", "https://genk.vn/eclick-ad"),
            ]
        return []


class FakeTopDevArticle:
    def __init__(self, title, href):
        self.title = title
        self.href = href

    def find_elements(self, by, selector):
        if selector == "h3.td-module-title":
            return [FakeElement(text=self.title)]
        if selector == "h3.td-module-title a":
            return [FakeElement(attrs={"href": self.href})]
        return []


class FakeTopDevDriver:
    def __init__(self, no_such_exc):
        self.no_such_exc = no_such_exc
        self.current_url = ""

    def get(self, url):
        self.current_url = url

    def quit(self):
        return None

    def execute_script(self, script, *args):
        return None

    def find_element(self, by, selector):
        if (
            by == "id"
            and selector == "fck_detail_gallery"
            and self.current_url.startswith("https://topdev.vn/post-")
        ):
            return _FakeParagraphContainer(["Doan 1", "Doan 2"])
        raise self.no_such_exc(selector)

    def find_elements(self, by, selector):
        if selector == "div.td-animation-stack":
            return [
                FakeTopDevArticle("TopDev Post 1", "https://topdev.vn/post-1"),
                FakeTopDevArticle("TopDev Post 2", "https://topdev.vn/post-2"),
            ]
        return []


def test_genk_scrape_writes_raw_output(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[2]
    script = root / "src" / "data-pipeline" / "scrape_from_GenK.py"

    no_such_exc = install_fake_selenium(monkeypatch, fake_driver=None)
    driver = FakeGenKDriver(no_such_exc)
    install_fake_selenium(monkeypatch, driver)

    monkeypatch.setattr(time, "sleep", lambda *_: None)
    monkeypatch.chdir(tmp_path)

    runpy.run_path(str(script), run_name="__main__")

    output = tmp_path / "raw_data" / "raw_data_GenK.json"
    assert output.exists()

    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["source_platform"] == "GenK-Trang thông tin điện tử từ tổng hợp"
    assert len(data["post_detail"]) == 2
    assert all("title" in p for p in data["post_detail"])
    assert all("content" in p for p in data["post_detail"])


def test_topdev_scrape_writes_output_file(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[2]
    script = root / "src" / "data-pipeline" / "scrape_from_TopDev.py"

    no_such_exc = install_fake_selenium(monkeypatch, fake_driver=None)
    driver = FakeTopDevDriver(no_such_exc)
    install_fake_selenium(monkeypatch, driver)

    monkeypatch.setattr(time, "sleep", lambda *_: None)
    monkeypatch.chdir(tmp_path)

    runpy.run_path(str(script), run_name="__main__")

    output = tmp_path / "raw_data" / "titles_TopDev2.json"
    assert output.exists()

    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["source_platform"] == "TopDev-Việc làm IT hàng đầu Việt Nam"
    assert isinstance(data["post_detail"], list)
    assert len(data["post_detail"]) == 2
    titles = [p["title"] for p in data["post_detail"]]
    assert titles == ["TopDev Post 1", "TopDev Post 2"]
    assert "title" in data["post_detail"][0]
    assert "content" in data["post_detail"][0]


def test_genk_filters_duplicate_and_ad_links_explicitly(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[2]
    script = root / "src" / "data-pipeline" / "scrape_from_GenK.py"

    class _Driver(FakeGenKDriver):
        def find_elements(self, by, selector):
            if selector == "a.btnviewmore":
                return [FakeElement(text="Xem thêm")]
            if selector == "div.elp-list":
                return [
                    FakeGenKArticle("Bai 1", "https://genk.vn/article-1"),
                    FakeGenKArticle("Bai 1 duplicate", "https://genk.vn/article-1"),
                    FakeGenKArticle("Ad", "https://genk.vn/eclick-ad"),
                    FakeGenKArticle("Bai 2", "https://genk.vn/article-2"),
                ]
            return []

    no_such_exc = install_fake_selenium(monkeypatch, fake_driver=None)
    driver = _Driver(no_such_exc)
    install_fake_selenium(monkeypatch, driver)
    monkeypatch.setattr(time, "sleep", lambda *_: None)
    monkeypatch.chdir(tmp_path)

    runpy.run_path(str(script), run_name="__main__")

    output = tmp_path / "raw_data" / "raw_data_GenK.json"
    data = json.loads(output.read_text(encoding="utf-8"))
    titles = [p["title"] for p in data["post_detail"]]
    assert titles == ["Bai 1", "Bai 2"]


def test_genk_all_articles_missing_content_returns_empty_post_detail(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[2]
    script = root / "src" / "data-pipeline" / "scrape_from_GenK.py"

    class _Driver(FakeGenKDriver):
        def find_element(self, by, selector):
            raise self.no_such_exc(selector)

    no_such_exc = install_fake_selenium(monkeypatch, fake_driver=None)
    driver = _Driver(no_such_exc)
    install_fake_selenium(monkeypatch, driver)
    monkeypatch.setattr(time, "sleep", lambda *_: None)
    monkeypatch.chdir(tmp_path)

    runpy.run_path(str(script), run_name="__main__")

    output = tmp_path / "raw_data" / "raw_data_GenK.json"
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["post_detail"] == []


def test_topdev_all_articles_missing_content_returns_empty_post_detail(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[2]
    script = root / "src" / "data-pipeline" / "scrape_from_TopDev.py"

    class _Driver(FakeTopDevDriver):
        def find_element(self, by, selector):
            raise self.no_such_exc(selector)

    no_such_exc = install_fake_selenium(monkeypatch, fake_driver=None)
    driver = _Driver(no_such_exc)
    install_fake_selenium(monkeypatch, driver)
    monkeypatch.setattr(time, "sleep", lambda *_: None)
    monkeypatch.chdir(tmp_path)

    runpy.run_path(str(script), run_name="__main__")

    output = tmp_path / "raw_data" / "titles_TopDev2.json"
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["post_detail"] == []
