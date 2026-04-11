import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest


pytestmark = pytest.mark.fast


ROOT = Path(__file__).resolve().parents[2]


def _load_module(module_name: str, relative_path: str):
    file_path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _install_fake_ner_dependencies(monkeypatch):
    torch_mod = types.ModuleType("torch")

    class _Cuda:
        @staticmethod
        def is_available():
            return False

    torch_mod.cuda = _Cuda()

    transformers_mod = types.ModuleType("transformers")

    class _AutoTokenizer:
        @staticmethod
        def from_pretrained(_):
            return object()

    class _AutoModelForTokenClassification:
        @staticmethod
        def from_pretrained(_):
            return object()

    def _pipeline(*args, **kwargs):
        def _runner(_text):
            return []

        return _runner

    transformers_mod.AutoTokenizer = _AutoTokenizer
    transformers_mod.AutoModelForTokenClassification = _AutoModelForTokenClassification
    transformers_mod.pipeline = _pipeline

    monkeypatch.setitem(sys.modules, "torch", torch_mod)
    monkeypatch.setitem(sys.modules, "transformers", transformers_mod)


def test_extract_rule_based_and_grouping_large_scenario(monkeypatch):
    _install_fake_ner_dependencies(monkeypatch)
    extract_papers = _load_module("extract_papers_module_a", "src/data-pipeline/extract_data_papers.py")

    assert extract_papers.normalize_entity("\u2581openai", label="PER") == "Openai"
    assert extract_papers.normalize_entity(" (Google). ", label="ORG") == "Google"

    text = "Ngay 12/03/2026, OpenAI dung Python tren AWS va AI Agent. toi gap ai do"
    dates = extract_papers.extract_date_entities(text)
    techs = extract_papers.extract_tech_entities(text)

    assert any(d["entity"] == "12/03/2026" and d["label"] == "DATE" for d in dates)
    tech_names = {t["entity"].lower() for t in techs}
    assert "python" in tech_names
    assert "aws" in tech_names
    assert "ai" in tech_names

    grouped = extract_papers.group_entities(
        [
            {"entity": "OpenAI", "label": "B-ORGANIZATION"},
            {"entity": "OpenAI", "label": "I-ORGANIZATION"},
            {"entity": "Sam Altman", "label": "PERSON"},
            {"entity": "Ha Noi", "label": "LOC"},
            {"entity": "03/2026", "label": "DATE"},
            {"entity": "Python", "label": "TECH"},
            {"entity": "ignored", "label": "UNKNOWN_LABEL"},
        ]
    )

    assert grouped["ORG"] == ["OpenAI"]
    assert grouped["PER"] == ["Sam Altman"]
    assert grouped["LOC"] == ["Ha Noi"]
    assert grouped["DATE"] == ["03/2026"]
    assert grouped["TECH"] == ["Python"]


def test_extract_entities_ner_large_scenario_with_valid_and_invalid_model_outputs(monkeypatch):
    _install_fake_ner_dependencies(monkeypatch)
    extract_papers = _load_module("extract_papers_module_b", "src/data-pipeline/extract_data_papers.py")

    monkeypatch.setattr(
        extract_papers,
        "ner_pipeline",
        lambda _text: [
            {"word": "", "entity_group": "ORG", "score": 0.9},
            {"word": "John", "entity_group": "O", "score": 0.8},
            {"word": "OpenAI", "entity_group": "ORG"},
            {"word": "Google", "entity_group": "ORG", "score": 0.88},
            {"word": "Sam Altman", "entity_group": "PER", "score": 0.92},
        ],
    )

    entities = extract_papers.extract_entities_ner("Google cong bo ngay 12/03/2026 voi Python")
    labels = {e["label"] for e in entities}

    assert "ORG" in labels
    assert "PER" in labels
    assert "DATE" in labels
    assert "TECH" in labels
    assert any(e["entity"] == "Google" for e in entities if e["label"] == "ORG")
    assert not any(e["entity"] == "John" for e in entities if e["label"] == "ORG")


def test_ner_json_file_and_topcv_extract_end_to_end_scenario(tmp_path, monkeypatch):
    _install_fake_ner_dependencies(monkeypatch)
    extract_papers = _load_module("extract_papers_module_c", "src/data-pipeline/extract_data_papers.py")
    extract_topcv = _load_module("extract_topcv_module", "src/data-pipeline/extract_data_topCV.py")

    papers_payload = {
        "source_platform": "VnExpress",
        "post_detail": [
            {"title": "OpenAI ra mat", "description": "Noi dung", "is_relevant": True},
            {"title": "Khong lien quan", "description": "Noi dung", "is_relevant": False},
        ],
    }

    papers_in = tmp_path / "filtered_data_DT.json"
    papers_in.write_text(json.dumps(papers_payload, ensure_ascii=False), encoding="utf-8")

    extract_papers.EXTRACTED_DATA_DIR = str(tmp_path)
    monkeypatch.setattr(
        extract_papers,
        "extract_entities_ner",
        lambda _text: [
            {"entity": "OpenAI", "label": "ORG", "score": 0.95},
            {"entity": "Python", "label": "TECH", "score": 1.0},
        ],
    )

    papers_out_path = extract_papers.ner_json_file_phobert(str(papers_in))
    papers_out = json.loads(Path(papers_out_path).read_text(encoding="utf-8"))

    assert Path(papers_out_path).name == "extracted_data_phobert_DT.json"
    assert len(papers_out["post_detail"]) == 1
    assert papers_out["post_detail"][0]["entities"]["ORG"] == ["OpenAI"]
    assert papers_out["post_detail"][0]["entities"]["TECH"] == ["Python"]

    no_relevant_payload = {
        "source_platform": "VnExpress",
        "post_detail": [
            {"title": "A", "description": "B", "is_relevant": False},
            {"title": "C", "description": "D", "is_relevant": False},
        ],
    }
    no_relevant_in = tmp_path / "filtered_data_VN-EP.json"
    no_relevant_in.write_text(json.dumps(no_relevant_payload, ensure_ascii=False), encoding="utf-8")

    no_relevant_out_path = extract_papers.ner_json_file_phobert(str(no_relevant_in))
    no_relevant_out = json.loads(Path(no_relevant_out_path).read_text(encoding="utf-8"))
    assert Path(no_relevant_out_path).name == "extracted_data_phobert_VN-EP.json"
    assert no_relevant_out["post_detail"] == []

    topcv_payload = {
        "post_detail": [
            {
                "title": "Python Developer",
                "created_at": "01/04/2026",
                "ORG": "ACME",
                "LOC": ["Ha Noi"],
                "DEADLINE_DATE": "30/04/2026",
                "SALARY": "20 - 30 trieu",
                "JOB_ROLE": "Backend Developer",
                "SKILL/TECH": ["Python", "FastAPI"],
                "is_relevant": True,
            },
            {
                "title": "Graphic Designer",
                "created_at": "01/04/2026",
                "ORG": "ACME",
                "LOC": ["Ha Noi"],
                "DEADLINE_DATE": "30/04/2026",
                "SALARY": "10 - 15 trieu",
                "JOB_ROLE": "Designer",
                "SKILL/TECH": ["Photoshop"],
                "is_relevant": False,
            },
        ]
    }
    topcv_in = tmp_path / "filtered_data_topCV.json"
    topcv_in.write_text(json.dumps(topcv_payload, ensure_ascii=False), encoding="utf-8")

    extract_topcv.EXTRACTED_DATA_DIR = str(tmp_path)
    topcv_out_path = extract_topcv.extract_topcv(str(topcv_in))
    topcv_out = json.loads(Path(topcv_out_path).read_text(encoding="utf-8"))

    assert len(topcv_out["post_detail"]) == 1
    assert topcv_out["post_detail"][0]["entities"]["ORG"] == ["ACME"]
    assert topcv_out["post_detail"][0]["entities"]["JOB_ROLE"] == ["Backend Developer"]


def test_extract_topcv_raises_when_core_fields_are_not_strings(tmp_path):
    extract_topcv = _load_module("extract_topcv_module_error", "src/data-pipeline/extract_data_topCV.py")

    payload = {
        "post_detail": [
            {
                "title": "Python Developer",
                "created_at": "01/04/2026",
                "ORG": None,
                "LOC": ["Ha Noi"],
                "DEADLINE_DATE": "30/04/2026",
                "SALARY": "20 - 30 trieu",
                "JOB_ROLE": "Backend Developer",
                "SKILL/TECH": ["Python"],
                "is_relevant": True,
            }
        ]
    }

    in_file = tmp_path / "filtered_data_topCV.json"
    in_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    extract_topcv.EXTRACTED_DATA_DIR = str(tmp_path)

    with pytest.raises(AttributeError):
        extract_topcv.extract_topcv(str(in_file))


def test_tech_case_sensitivity_and_extract_edge_cases(tmp_path, monkeypatch):
    _install_fake_ner_dependencies(monkeypatch)
    extract_papers = _load_module("extract_papers_module_d", "src/data-pipeline/extract_data_papers.py")
    extract_topcv = _load_module("extract_topcv_module_edge", "src/data-pipeline/extract_data_topCV.py")

    # --- TECH_ABBREVS_CASE_SENSITIVE: "AI" matches, "ai" (lowercase) does NOT ---
    text_upper = "Ứng dụng AI trong y tế"
    text_lower = "toi gap ai do hom nay"
    techs_upper = extract_papers.extract_tech_entities(text_upper)
    techs_lower = extract_papers.extract_tech_entities(text_lower)
    assert any(t["entity"] == "AI" for t in techs_upper)
    assert not any(t["entity"].upper() == "AI" for t in techs_lower)

    # --- TECH_ABBREVS (case-insensitive): "aws" matches even lowercase ---
    techs_aws = extract_papers.extract_tech_entities("Dùng aws để deploy")
    assert any(t["entity"].lower() == "aws" for t in techs_aws)

    # --- Overlapping date spans: longer date match should take priority ---
    text_date = "ngày 15 tháng 3 năm 2026 có sự kiện"
    dates = extract_papers.extract_date_entities(text_date)
    # Should have 1 merged date span, not separate "tháng 3" and "ngày 15 tháng 3 năm 2026"
    date_texts = [d["entity"] for d in dates]
    assert len(date_texts) >= 1
    longest = max(date_texts, key=len)
    assert "2026" in longest

    # --- extract_entities_ner with empty/whitespace text → empty list ---
    assert extract_papers.extract_entities_ner("") == []
    assert extract_papers.extract_entities_ner("   ") == []

    # --- normalize_entity: empty string, all-punctuation ---
    assert extract_papers.normalize_entity("") == ""
    assert extract_papers.normalize_entity("...,,,") == ""
    assert extract_papers.normalize_entity("  ▁▁  ") == ""

    # --- extract_topcv: non-existent file → returns empty string ---
    result = extract_topcv.extract_topcv("/nonexistent/path/file.json")
    assert result == ""

    # --- extract_topcv: file with empty post_detail → output has 0 posts ---
    empty_payload = {"post_detail": []}
    empty_file = tmp_path / "filtered_data_topCV_empty.json"
    empty_file.write_text(json.dumps(empty_payload, ensure_ascii=False), encoding="utf-8")
    extract_topcv.EXTRACTED_DATA_DIR = str(tmp_path)
    out_path = extract_topcv.extract_topcv(str(empty_file))
    out_data = json.loads(Path(out_path).read_text(encoding="utf-8"))
    assert out_data["post_detail"] == []
