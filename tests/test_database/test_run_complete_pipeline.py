from __future__ import annotations

import runpy
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UTILS_DIR = ROOT / "src" / "database" / "utils"


class FakeResult:
    def __init__(self, record):
        self.record = record

    def single(self):
        return self.record


class FakeSession:
    def __init__(self):
        self.run_calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def run(self, query):
        self.run_calls.append(query)
        if "as count" in query:
            return FakeResult({"count": 99})
        return FakeResult({"rel_count": 7})


class FakeDriver:
    def __init__(self):
        self.session_obj = FakeSession()
        self.closed = False
        self.session_calls = []

    def session(self, database=None):
        self.session_calls.append(database)
        return self.session_obj

    def close(self):
        self.closed = True


class FakeRelationshipBuilder:
    last_instance = None

    def __init__(self):
        FakeRelationshipBuilder.last_instance = self
        self.called_with = None

    def run_import_pipeline(self, news_paths, topcv_path=None):
        self.called_with = (news_paths, topcv_path)
        return {"imported": True}


def test_run_complete_pipeline_executes_import_and_relationship_steps(monkeypatch):
    fake_driver = FakeDriver()
    fake_neo4j_module = types.ModuleType("neo4j")
    fake_neo4j_module.GraphDatabase = types.SimpleNamespace(driver=lambda *args, **kwargs: fake_driver)

    fake_config_module = types.ModuleType("neo4j_config")
    fake_config_module.NEO4J_URI = "neo4j+s://example.databases.neo4j.io"
    fake_config_module.NEO4J_USERNAME = "neo4j"
    fake_config_module.NEO4J_PASSWORD = "secret"
    fake_config_module.NEO4J_DATABASE = "neo4j"

    fake_multi_source_module = types.ModuleType("multi_source_import_v3")
    fake_multi_source_module.RelationshipBuilder = FakeRelationshipBuilder
    fake_multi_source_module.main = None

    real_database_connection = __import__("src.database.utils.database_connection", fromlist=["dummy"])

    monkeypatch.setitem(sys.modules, "neo4j", fake_neo4j_module)
    monkeypatch.setitem(sys.modules, "neo4j_config", fake_config_module)
    monkeypatch.setitem(sys.modules, "multi_source_import_v3", fake_multi_source_module)
    monkeypatch.setitem(sys.modules, "database_connection", real_database_connection)

    if str(UTILS_DIR) not in sys.path:
        sys.path.insert(0, str(UTILS_DIR))

    runpy.run_path(str(UTILS_DIR / "run_complete_pipeline.py"), run_name="__main__")

    instance = FakeRelationshipBuilder.last_instance
    assert instance is not None
    assert len(instance.called_with[0]) == 2
    assert instance.called_with[1] is not None

    assert fake_driver.closed is True
    assert fake_driver.session_calls == ["neo4j", "neo4j"]
    assert len(fake_driver.session_obj.run_calls) == 12
    assert any("HIRES_FOR" in query for query in fake_driver.session_obj.run_calls)
    assert any("REQUIRES {is_mandatory: true, frequency: 1}" in query for query in fake_driver.session_obj.run_calls)
    assert any("USES {frequency: 1}" in query for query in fake_driver.session_obj.run_calls)
    assert any("MATCH (n:Article) RETURN count(n) as count" in query for query in fake_driver.session_obj.run_calls)
    assert any("MATCH ()-[r]->() RETURN count(r) as count" in query for query in fake_driver.session_obj.run_calls)
