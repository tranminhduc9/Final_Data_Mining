import importlib.util
import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.fast


def _load_module(module_name: str, relative_path: str):
    root = Path(__file__).resolve().parents[2]
    file_path = root / relative_path
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


filter_data = _load_module("filter_data_module", "src/data-pipeline/filter_data.py")


def test_keyword_and_topcv_validation_scenario_matrix():
    keyword_cases = [
        ("Tin AI m\u1edbi nh\u1ea5t", True),
        ("Hi\u1ec7n t\u01b0\u1ee3ng nguy\u1ec7t th\u1ef1c t\u1ed1i nay", False),
        ("M\u1ed9t ti\u00eau \u0111\u1ec1 trung t\u00ednh", None),
        ("AI v\u1ec1 hi\u1ec7n t\u01b0\u1ee3ng nguy\u1ec7t th\u1ef1c", False),
    ]
    for title, expected in keyword_cases:
        assert filter_data.keyword_filter(title) is expected

    posts = [
        {"ORG": "A", "DEADLINE_DATE": "01/01/2027"},
        {"ORG": "", "DEADLINE_DATE": "01/01/2027"},
        {"ORG": "B", "DEADLINE_DATE": ""},
        {"ORG": "C", "DEADLINE_DATE": "02/01/2027"},
    ]
    assert filter_data._remove_invalid_topcv_posts(posts) == [
        {"ORG": "A", "DEADLINE_DATE": "01/01/2027"},
        {"ORG": "C", "DEADLINE_DATE": "02/01/2027"},
    ]


def test_classify_batch_resilience_scenario(monkeypatch):
    class _RespEmpty:
        text = ""

    class _RespMismatch:
        text = "1. YES\n2. NO"

    call_count = {"n": 0}

    class _RespOk:
        text = "1. YES\n2. NO"

    class _ModelsEmpty:
        @staticmethod
        def generate_content(*args, **kwargs):
            return _RespEmpty()

    class _ModelsMismatch:
        @staticmethod
        def generate_content(*args, **kwargs):
            return _RespMismatch()

    class _ModelsRetry:
        @staticmethod
        def generate_content(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise Exception("429 rate limit")
            return _RespOk()

    class _Client:
        def __init__(self, models):
            self.models = models

    monkeypatch.setattr(filter_data, "client", _Client(_ModelsEmpty()))
    assert filter_data.classify_batch(["A", "B"]) == [False, False]

    monkeypatch.setattr(filter_data, "client", _Client(_ModelsMismatch()))
    assert filter_data.classify_batch(["A", "B", "C"]) == [False, False, False]

    monkeypatch.setattr(filter_data, "client", _Client(_ModelsRetry()))
    monkeypatch.setattr(filter_data.time, "sleep", lambda *_: None)
    assert filter_data.classify_batch(["A", "B"]) == [True, False]
    assert call_count["n"] == 2


def test_filter_json_file_end_to_end_with_topcv_cleanup_and_api_fallback(tmp_path, monkeypatch):
    payload = {
        "post_detail": [
            {"title": "AI b\u00f9ng n\u1ed5", "ORG": "A", "DEADLINE_DATE": "01/01/2027"},
            {"title": "Nguy\u1ec7t th\u1ef1c hi\u1ebfm g\u1eb7p", "ORG": "B", "DEADLINE_DATE": "02/01/2027"},
            {"title": "Ti\u00eau \u0111\u1ec1 m\u01a1 h\u1ed3 A", "ORG": "C", "DEADLINE_DATE": "03/01/2027"},
            {"title": "Ti\u00eau \u0111\u1ec1 m\u01a1 h\u1ed3 B", "ORG": "D", "DEADLINE_DATE": "04/01/2027"},
            {"title": "B\u1ecb lo\u1ea1i vi thieu ORG", "ORG": "", "DEADLINE_DATE": "05/01/2027"},
        ]
    }

    in_file = tmp_path / "cleaned_data_topCV.json"
    in_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    filter_data.FILTERED_DATA_DIR = str(tmp_path / "filtered")

    api_called = {"value": False}

    def _fake_run_api_filter(posts, need_api, results_map):
        api_called["value"] = True
        assert need_api == [2, 3]
        results_map[2] = True
        results_map[3] = False

    monkeypatch.setattr(filter_data, "_run_api_filter", _fake_run_api_filter)

    out_path = filter_data.filter_json_file(str(in_file))
    out = json.loads(Path(out_path).read_text(encoding="utf-8"))

    assert api_called["value"] is True
    assert Path(out_path).name == "filtered_data_topCV.json"
    assert len(out["post_detail"]) == 5
    assert out["post_detail"][0]["is_relevant"] is True
    assert out["post_detail"][1]["is_relevant"] is False
    assert out["post_detail"][2]["is_relevant"] is True
    assert out["post_detail"][3]["is_relevant"] is False


def test_collect_input_files_scan_and_missing_file_error(tmp_path):
    class _ArgsMissing:
        files = ["this_file_does_not_exist.json"]

    with pytest.raises(SystemExit):
        filter_data._collect_input_files(_ArgsMissing())

    cleaned_dir = tmp_path / "cleaned"
    cleaned_dir.mkdir()
    (cleaned_dir / "cleaned_data_A.json").write_text("{}", encoding="utf-8")
    (cleaned_dir / "note.txt").write_text("skip", encoding="utf-8")

    class _ArgsScan:
        files = []

    old_dir = filter_data.DIRECTORY
    try:
        filter_data.DIRECTORY = str(cleaned_dir)
        files = filter_data._collect_input_files(_ArgsScan())
        assert len(files) == 1
        assert Path(files[0]).name == "cleaned_data_A.json"
    finally:
        filter_data.DIRECTORY = old_dir


def test_api_retry_exhaustion_and_keyword_boundary_edge_cases(monkeypatch):
    # --- classify_batch: all 3 retries fail (429 every time) → returns all False ---
    call_count = {"n": 0}

    class _ModelsAlwaysFail:
        @staticmethod
        def generate_content(*args, **kwargs):
            call_count["n"] += 1
            raise Exception("429 rate limit exceeded")

    class _Client:
        def __init__(self, models):
            self.models = models

    monkeypatch.setattr(filter_data, "client", _Client(_ModelsAlwaysFail()))
    monkeypatch.setattr(filter_data.time, "sleep", lambda *_: None)
    result = filter_data.classify_batch(["Title A", "Title B"])
    assert result == [False, False]
    assert call_count["n"] == 3  # tried exactly MAX_RETRIES times

    # --- classify_batch: non-rate-limit exception → returns False immediately (no retry) ---
    non_rate_count = {"n": 0}

    class _ModelsNonRate:
        @staticmethod
        def generate_content(*args, **kwargs):
            non_rate_count["n"] += 1
            raise Exception("Connection timeout")

    monkeypatch.setattr(filter_data, "client", _Client(_ModelsNonRate()))
    result2 = filter_data.classify_batch(["X"])
    assert result2 == [False]
    assert non_rate_count["n"] == 1  # no retry for non-rate-limit errors

    # --- keyword_filter: regex word boundary (\\bJava\\b should NOT match "JavaScript") ---
    assert filter_data.keyword_filter("Lập trình JavaScript nâng cao") is True  # "JavaScript" is in whitelist
    # "Java" alone with \\b should match
    assert filter_data.keyword_filter("Tuyển dụng Java Developer") is True

    # --- make_batches ---
    assert filter_data.make_batches([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert filter_data.make_batches([], 3) == []

    # --- _resolve_output_path: cleaned_ prefix vs cleaned_data_ prefix ---
    path1 = filter_data._resolve_output_path("/tmp/cleaned_data_DT.json")
    assert Path(path1).name == "filtered_data_DT.json"

    path2 = filter_data._resolve_output_path("/tmp/cleaned_VN-EP.json")
    assert Path(path2).name == "filtered_data_VN-EP.json"
