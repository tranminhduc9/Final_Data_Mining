import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest


pytestmark = pytest.mark.fast


ROOT = Path(__file__).resolve().parents[2]


def _install_fake_classifier_dependencies(monkeypatch):
    torch_mod = types.ModuleType("torch")

    class _Cuda:
        @staticmethod
        def is_available():
            return False

    class _NoGrad:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

    class _ProbVector:
        def __init__(self, probs):
            self.probs = probs

        def __getitem__(self, idx):
            return _Scalar(self.probs[idx])

    class _SoftmaxResult:
        def __init__(self, probs):
            self.probs = probs

        def __getitem__(self, idx):
            return _ProbVector(self.probs)

    class _ArgMaxResult:
        def __init__(self, idx):
            self.idx = idx

        def item(self):
            return self.idx

    class _Scalar:
        def __init__(self, value):
            self.value = value

        def item(self):
            return self.value

    def _softmax(_logits, dim=-1):
        return _SoftmaxResult([0.2, 0.8])

    def _argmax(_probs, dim=-1):
        return _ArgMaxResult(1)

    torch_mod.cuda = _Cuda()
    torch_mod.device = lambda name: name
    torch_mod.no_grad = lambda: _NoGrad()
    torch_mod.softmax = _softmax
    torch_mod.argmax = _argmax

    transformers_mod = types.ModuleType("transformers")

    class _FakeBatch(dict):
        def to(self, _device):
            return self

    class _AutoTokenizer:
        @staticmethod
        def from_pretrained(_):
            class _Tokenizer:
                def __call__(self, *args, **kwargs):
                    return _FakeBatch()

            return _Tokenizer()

    class _AutoModelForSequenceClassification:
        @staticmethod
        def from_pretrained(_):
            class _Model:
                def eval(self):
                    return self

                def to(self, _device):
                    return self

                def __call__(self, **kwargs):
                    return types.SimpleNamespace(logits=[[0.2, 0.8]])

            return _Model()

    transformers_mod.AutoTokenizer = _AutoTokenizer
    transformers_mod.AutoModelForSequenceClassification = _AutoModelForSequenceClassification

    underthesea_mod = types.ModuleType("underthesea")
    underthesea_mod.word_tokenize = lambda text, format="text": text
    underthesea_mod.ner = lambda _text: []

    monkeypatch.setitem(sys.modules, "torch", torch_mod)
    monkeypatch.setitem(sys.modules, "transformers", transformers_mod)
    monkeypatch.setitem(sys.modules, "underthesea", underthesea_mod)


def _load_filter_data(monkeypatch):
    _install_fake_classifier_dependencies(monkeypatch)
    file_path = ROOT / "src/data-pipeline/filter_data.py"
    spec = importlib.util.spec_from_file_location("filter_data_module", file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_preprocess_title_handles_ner_and_normalization(monkeypatch):
    filter_data = _load_filter_data(monkeypatch)

    monkeypatch.setattr(
        filter_data,
        "ner",
        lambda _text: [
            ("OpenAI", "Np", "B-NP", "B-ORG"),
            ("Ha Noi", "Np", "B-NP", "B-LOC"),
        ],
    )
    monkeypatch.setattr(filter_data, "word_tokenize", lambda text, format="text": text)

    out = filter_data.preprocess_title("OpenAI tăng 12% tại Ha Noi năm 2026")

    assert "name" in out
    assert "loc" in out
    assert "percent" in out
    assert "date" in out


def test_classify_titles_uses_predict_one_results(monkeypatch):
    filter_data = _load_filter_data(monkeypatch)

    seq = iter([(True, 0.9), (False, 0.8), (True, 0.7)])
    monkeypatch.setattr(filter_data, "predict_one", lambda _t: next(seq))

    out = filter_data.classify_titles(["a", "b", "c"])
    assert out == [True, False, True]


def test_resolve_output_path_prefix_conversion(monkeypatch, tmp_path):
    filter_data = _load_filter_data(monkeypatch)
    monkeypatch.setattr(filter_data, "FILTERED_DATA_DIR", str(tmp_path / "filtered"))

    p1 = filter_data._resolve_output_path("/tmp/raw_data_DT.json")
    p2 = filter_data._resolve_output_path("/tmp/custom.json")

    assert Path(p1).name == "filtered_data_DT.json"
    assert Path(p2).name == "filtered_data_custom.json"


def test_filter_json_file_adds_is_relevant_and_writes_output(monkeypatch, tmp_path):
    filter_data = _load_filter_data(monkeypatch)

    payload = {
        "source_platform": "Demo",
        "post_detail": [
            {"title": "A", "content": "x"},
            {"title": "B", "content": "y"},
            {"title": "C", "content": "z"},
        ],
    }
    in_file = tmp_path / "raw_data_demo.json"
    in_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(filter_data, "FILTERED_DATA_DIR", str(tmp_path / "filtered"))
    seq = iter([(True, 0.9), (False, 0.8), (True, 0.7)])
    monkeypatch.setattr(filter_data, "predict_one", lambda _t: next(seq))

    out_path = filter_data.filter_json_file(str(in_file))
    out = json.loads(Path(out_path).read_text(encoding="utf-8"))

    assert Path(out_path).name == "filtered_data_demo.json"
    assert [p["is_relevant"] for p in out["post_detail"]] == [True, False, True]


def test_filter_json_file_returns_empty_for_no_posts(monkeypatch, tmp_path):
    filter_data = _load_filter_data(monkeypatch)

    payload = {"post_detail": []}
    in_file = tmp_path / "raw_data_empty.json"
    in_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    assert filter_data.filter_json_file(str(in_file)) == ""


def test_main_handles_no_input_files(monkeypatch, tmp_path):
    filter_data = _load_filter_data(monkeypatch)

    monkeypatch.setattr(filter_data.glob, "glob", lambda _pattern: [])
    monkeypatch.setattr(filter_data, "RAW_DATA_DIR", str(tmp_path))

    filter_data.main()


def test_preprocess_title_returns_empty_for_invalid_inputs(monkeypatch):
    filter_data = _load_filter_data(monkeypatch)
    monkeypatch.setattr(filter_data, "word_tokenize", lambda text, format="text": text)

    assert filter_data.preprocess_title("") == ""
    assert filter_data.preprocess_title(None) == ""
    assert filter_data.preprocess_title(123) == ""


def test_preprocess_title_continues_when_ner_raises(monkeypatch):
    filter_data = _load_filter_data(monkeypatch)
    monkeypatch.setattr(filter_data, "word_tokenize", lambda text, format="text": text)

    monkeypatch.setattr(filter_data, "ner", lambda _text: (_ for _ in ()).throw(RuntimeError("ner down")))
    out = filter_data.preprocess_title("Bài viết 12/03/2026 tăng 15% trong Quý 2 năm 2025")
    assert "date" in out
    assert "percent" in out


def test_filter_json_file_preserves_metadata(monkeypatch, tmp_path):
    filter_data = _load_filter_data(monkeypatch)

    payload = {
        "source_platform": "DemoPlatform",
        "source_url": "https://example.com/feed",
        "scraped_at": "2026-04-18 10:30:45",
        "post_detail": [
            {"title": "A"},
            {"title": "B"},
            {"title": "C"},
        ],
    }
    in_file = tmp_path / "raw_data_meta.json"
    in_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(filter_data, "FILTERED_DATA_DIR", str(tmp_path / "filtered"))
    monkeypatch.setattr(filter_data, "predict_one", lambda _t: (False, 0.88))

    out_path = filter_data.filter_json_file(str(in_file))
    out = json.loads(Path(out_path).read_text(encoding="utf-8"))

    assert out["source_platform"] == payload["source_platform"]
    assert out["source_url"] == payload["source_url"]
    assert out["scraped_at"] == payload["scraped_at"]


def test_filter_json_file_marks_all_non_it_false(monkeypatch, tmp_path):
    filter_data = _load_filter_data(monkeypatch)

    payload = {
        "source_platform": "DemoPlatform",
        "source_url": "https://example.com/feed",
        "scraped_at": "2026-04-18 10:30:45",
        "post_detail": [
            {"title": "A"},
            {"title": "B"},
            {"title": "C"},
        ],
    }
    in_file = tmp_path / "raw_data_meta.json"
    in_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(filter_data, "FILTERED_DATA_DIR", str(tmp_path / "filtered"))
    monkeypatch.setattr(filter_data, "predict_one", lambda _t: (False, 0.88))

    out_path = filter_data.filter_json_file(str(in_file))
    out = json.loads(Path(out_path).read_text(encoding="utf-8"))

    assert [p["is_relevant"] for p in out["post_detail"]] == [False, False, False]
