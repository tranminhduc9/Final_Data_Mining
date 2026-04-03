import json
import random
import runpy
import time
from pathlib import Path

import pytest

from conftest import FakeElement, install_fake_selenium


pytestmark = pytest.mark.scrape


class FakeTopCVDriver:
    def __init__(self, no_such_exc, with_noise=False, invalid_deadline=False, failing_link=None):
        self.no_such_exc = no_such_exc
        self.current_url = ""
        self.with_noise = with_noise
        self.invalid_deadline = invalid_deadline
        self.failing_link = failing_link
        self.jobs = {
            "https://job/1": {
                "title": "Backend Developer",
                "deadline": "20/04/2026",
                "org": "ACME",
                "salary": "20 - 30 triệu",
                "loc": ["Hà Nội"],
                "skills": ["Python", "FastAPI"],
            },
            "https://job/2": {
                "title": "QA Engineer",
                "deadline": "22/04/2026" if not invalid_deadline else "invalid-date",
                "org": "Beta Corp",
                "salary": "Thoả thuận",
                "loc": ["Hồ Chí Minh"],
                "skills": ["Selenium"],
            },
        }

    def get(self, url):
        if self.failing_link and url == self.failing_link:
            raise RuntimeError("forced page error")
        self.current_url = url

    def quit(self):
        return None

    def find_element(self, by, selector):
        if selector == "a.header-menu-mobile__logo img":
            return FakeElement(attrs={"title": "TopCV"})

        if self.current_url in self.jobs:
            job = self.jobs[self.current_url]
            if selector == "h1.job-detail__info--title":
                return FakeElement(text=job["title"])
            if selector == "div.job-detail__info--deadline-date":
                return FakeElement(text=job["deadline"])
            if selector == "div.company-name-label a":
                return FakeElement(text=job["org"])
            if selector == "div.job-detail__info--section-content-value":
                return FakeElement(text=job["salary"])

        raise self.no_such_exc(selector)

    def find_elements(self, by, selector):
        if selector == "h3.title a":
            if self.with_noise:
                return [
                    FakeElement(attrs={"href": "https://job/1"}),
                    FakeElement(attrs={"href": "https://job/1"}),
                    FakeElement(attrs={"href": ""}),
                    FakeElement(attrs={"href": "https://job/2"}),
                ]
            return [
                FakeElement(attrs={"href": "https://job/1"}),
                FakeElement(attrs={"href": "https://job/2"}),
            ]

        if self.current_url in self.jobs:
            job = self.jobs[self.current_url]
            if selector == "div.job-detail__info--section-content-value a":
                return [FakeElement(text=x) for x in job["loc"]]
            if selector == "h1.job-detail__info--title a":
                return []
            if selector == "div.box-category.collapsed span":
                return [FakeElement(text=x) for x in job["skills"]]

        return []


def test_topcv_scrape_end_to_end_basic_output(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[2]
    script = root / "src" / "data-pipeline" / "scrape_from_topCV.py"
    no_such_exc = install_fake_selenium(monkeypatch, fake_driver=None)
    driver = FakeTopCVDriver(no_such_exc)
    install_fake_selenium(monkeypatch, driver)

    monkeypatch.setattr(time, "sleep", lambda *_: None)
    monkeypatch.setattr(random, "uniform", lambda a, b: a)
    monkeypatch.setattr(random, "randint", lambda a, b: 30)
    monkeypatch.chdir(tmp_path)

    runpy.run_path(str(script), run_name="__main__")
    
    output_path = tmp_path / "raw_data" / "raw_data_topCV.json"
    assert output_path.exists()
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["source_platform"] == "TopCV"
    assert len(data["post_detail"]) == 2
    assert all("JOB_ROLE" in p and "DEADLINE_DATE" in p for p in data["post_detail"])


def test_topcv_scrape_noise_and_invalid_date_scenario(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[2]
    script = root / "src" / "data-pipeline" / "scrape_from_topCV.py"
    no_such_exc = install_fake_selenium(monkeypatch, fake_driver=None)
    driver = FakeTopCVDriver(no_such_exc, with_noise=True, invalid_deadline=True)
    install_fake_selenium(monkeypatch, driver)

    monkeypatch.setattr(time, "sleep", lambda *_: None)
    monkeypatch.setattr(random, "uniform", lambda a, b: a)
    monkeypatch.setattr(random, "randint", lambda a, b: 30)
    monkeypatch.chdir(tmp_path)

    runpy.run_path(str(script), run_name="__main__")
    
    output_path = tmp_path / "raw_data" / "raw_data_topCV.json"
    data = json.loads(output_path.read_text(encoding="utf-8"))

    assert len(data["post_detail"]) == 2
    invalid_date_item = next(item for item in data["post_detail"] if item["DEADLINE_DATE"] == "invalid-date")
    assert invalid_date_item["created_at"] == "invalid-date"


def test_topcv_scrape_continues_when_one_job_page_fails(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[2]
    script = root / "src" / "data-pipeline" / "scrape_from_topCV.py"
    no_such_exc = install_fake_selenium(monkeypatch, fake_driver=None)
    driver = FakeTopCVDriver(no_such_exc, failing_link="https://job/2")
    install_fake_selenium(monkeypatch, driver)

    monkeypatch.setattr(time, "sleep", lambda *_: None)
    monkeypatch.setattr(random, "uniform", lambda a, b: a)
    monkeypatch.setattr(random, "randint", lambda a, b: 30)
    monkeypatch.chdir(tmp_path)

    runpy.run_path(str(script), run_name="__main__")
    
    output_path = tmp_path / "raw_data" / "raw_data_topCV.json"
    data = json.loads(output_path.read_text(encoding="utf-8"))

    assert len(data["post_detail"]) == 1
    assert data["post_detail"][0]["title"] == "Backend Developer"
