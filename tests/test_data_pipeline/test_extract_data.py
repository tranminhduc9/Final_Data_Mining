import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest


pytestmark = pytest.mark.fast


ROOT = Path(__file__).resolve().parents[2]


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
            class _Tokenizer:
                @staticmethod
                def encode(text, add_special_tokens=False):
                    return [1, 2, 3]

                @staticmethod
                def decode(token_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True):
                    return " ".join(str(t) for t in token_ids)

            return _Tokenizer()

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


def _load_extract_data(monkeypatch, module_name):
    _install_fake_ner_dependencies(monkeypatch)
    file_path = ROOT / "src/data-pipeline/extract_data.py"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_rule_based_extractors_find_basic_entities(monkeypatch):
    extract_data = _load_extract_data(monkeypatch, "extract_data_module_a")

    text = "Ngay 12/03/2026, OpenAI dung Python tren AWS. Tuyen Data Engineer luong 20 - 30 trieu"
    dates = extract_data.extract_date_entities(text)
    techs = extract_data.extract_tech_entities(text)
    jobs = extract_data.extract_job_role_entities(text)
    salaries = extract_data.extract_salary_entities(text)

    assert any("12/03/2026" in d["entity"] for d in dates)
    assert any(t["entity"].lower() == "python" for t in techs)
    assert any(t["entity"].lower() == "aws" for t in techs)
    assert any(j["entity"].lower() == "data engineer" for j in jobs)
    assert any("20 - 30" in s["entity"] for s in salaries)


def test_group_entities_normalizes_and_deduplicates(monkeypatch):
    extract_data = _load_extract_data(monkeypatch, "extract_data_module_a2")

    grouped = extract_data.group_entities(
        [
            {"entity": "OpenAI", "label": "B-ORGANIZATION"},
            {"entity": "OpenAI", "label": "I-ORGANIZATION"},
            {"entity": "Sam Altman", "label": "PERSON"},
            {"entity": "Ha Noi", "label": "LOC"},
            {"entity": "Python", "label": "TECH"},
            {"entity": "20 - 30 triệu", "label": "SALARY"},
        ]
    )

    assert grouped["ORG"] == ["OpenAI"]
    assert grouped["PER"] == ["Sam Altman"]
    assert grouped["LOC"] == ["Ha Noi"]
    assert grouped["TECH"] == ["Python"]
    assert grouped["SALARY"] == ["20 - 30 triệu"]


def test_chunk_text_by_tokens_sliding_window(monkeypatch):
    extract_data = _load_extract_data(monkeypatch, "extract_data_module_b")

    class _FakeTokenizer:
        @staticmethod
        def encode(_text, add_special_tokens=False):
            return list(range(12))

        @staticmethod
        def decode(token_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True):
            return " ".join(str(t) for t in token_ids)

    monkeypatch.setattr(extract_data, "_tokenizer", _FakeTokenizer())

    chunks = extract_data._chunk_text_by_tokens("dummy", max_tokens=5, overlap=2)

    assert chunks == [
        "0 1 2 3 4",
        "3 4 5 6 7",
        "6 7 8 9 10",
        "9 10 11",
    ]


def test_extract_entities_ner_includes_rule_based_entities(monkeypatch):
    extract_data = _load_extract_data(monkeypatch, "extract_data_module_c")

    monkeypatch.setattr(extract_data, "_chunk_text_by_tokens", lambda *_a, **_k: ["chunk"])
    monkeypatch.setattr(
        extract_data,
        "ner_pipeline",
        lambda _chunk: [{"word": "OpenAI", "entity_group": "ORG", "score": 0.91}],
    )

    text = "OpenAI tuyển Data Engineer, lương 25 triệu"
    entities = extract_data.extract_entities_ner(text)
    labels = {e["label"] for e in entities}

    assert "ORG" in labels
    assert "JOB_ROLE" in labels
    assert "SALARY" in labels


def test_ner_json_file_writes_only_relevant_posts(monkeypatch, tmp_path):
    extract_data = _load_extract_data(monkeypatch, "extract_data_module_d")

    payload = {
        "source_platform": "VnExpress",
        "post_detail": [
            {"title": "OpenAI ra mat", "content": "Noi dung", "is_relevant": True},
            {"title": "Khong lien quan", "content": "Noi dung", "is_relevant": False},
        ],
    }
    in_file = tmp_path / "filtered_data_VN-EP.json"
    in_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    extract_data.EXTRACTED_DATA_DIR = str(tmp_path)
    monkeypatch.setattr(
        extract_data,
        "extract_entities_ner",
        lambda _text: [
            {"entity": "OpenAI", "label": "ORG", "score": 0.95},
            {"entity": "Python", "label": "TECH", "score": 1.0},
        ],
    )

    out_path = extract_data.ner_json_file_phobert(str(in_file))
    out = json.loads(Path(out_path).read_text(encoding="utf-8"))

    assert Path(out_path).name == "extracted_data_phobert_VN-EP.json"
    assert len(out["post_detail"]) == 1
    assert out["post_detail"][0]["entities"]["ORG"] == ["OpenAI"]
    assert out["post_detail"][0]["entities"]["TECH"] == ["Python"]


def test_main_returns_when_no_input_files(monkeypatch, tmp_path):
    extract_data = _load_extract_data(monkeypatch, "extract_data_module_e")

    monkeypatch.setattr(sys, "argv", ["extract_data.py", "--dir", str(tmp_path)])
    extract_data.main()


def test_normalize_entity_extended_cases(monkeypatch):
    extract_data = _load_extract_data(monkeypatch, "extract_data_module_f")

    # Kiểm tra chuẩn hóa thực thể.
    assert extract_data.normalize_entity(" ▁John Doe.", label="PER") == "John Doe"
    assert extract_data.normalize_entity("...", label="ORG") == ""
    assert extract_data.normalize_entity("", label="PER") == ""


def test_normalize_entity_title_cases_lowercased_person(monkeypatch):
    extract_data = _load_extract_data(monkeypatch, "extract_data_module_f_per")

    # PER label với toàn chữ thường → title-case. Ví dụ: "nguyen van a" → "Nguyen Van A".
    assert extract_data.normalize_entity("nguyen van a", label="PER") == "Nguyen Van A"
    assert extract_data.normalize_entity("tran thi b", label="PER") == "Tran Thi B"
    # Không title-case nếu không phải label PER
    assert extract_data.normalize_entity("nguyen van a", label="ORG") == "nguyen van a"
    # Không title-case nếu có chữ hoa (đã có chuẩn hóa riêng)
    assert extract_data.normalize_entity("Nguyen VAN a", label="PER") == "Nguyen VAN a"


def test_extract_salary_detailed_usd_range_format(monkeypatch):
    extract_data = _load_extract_data(monkeypatch, "extract_data_module_f_salary")

    # SALARY: chi tiết USD range format "$X,XXX - $Y,XXX USD" (pattern 4).
    text = "Salary package: $2,000 - $3,000 USD, salary negotiable"
    salaries = extract_data.extract_salary_entities(text)
    salary_values = [s["entity"].lower() for s in salaries]
    # Đảm bảo capture chính xác toàn bộ "$2,000 - $3,000 USD" (có USD suffix)
    assert any("$2,000 - $3,000 usd" in v for v in salary_values)
    # Pattern 7: "salary negotiable/competitive/attractive"
    assert any("salary negotiable" in v for v in salary_values)


def test_extract_tech_case_and_dedup(monkeypatch):
    extract_data = _load_extract_data(monkeypatch, "extract_data_module_f2")

    # TECH: phân biệt AI viết hoa và ai viết thường, đồng thời loại trùng.
    techs = extract_data.extract_tech_entities("AI và ai và AI dùng Python và python")
    tech_values = [t["entity"] for t in techs]
    assert any(v == "AI" for v in tech_values)
    assert not any(v == "ai" for v in tech_values)
    assert sum(1 for v in tech_values if v.lower() == "python") == 1


def test_extract_date_vietnamese_and_quarter_forms(monkeypatch):
    extract_data = _load_extract_data(monkeypatch, "extract_data_module_f3")

    # DATE: dạng tiếng Việt đầy đủ và dạng quý.
    dates = extract_data.extract_date_entities("Sự kiện ngày 12 tháng 3 năm 2026, Quý II/2025")
    date_values = [d["entity"] for d in dates]
    assert any("ngày 12 tháng 3 năm 2026".lower() in v.lower() for v in date_values)
    assert any("Quý II/2025".lower() in v.lower() for v in date_values)


def test_extract_salary_usd_and_negotiable_forms(monkeypatch):
    extract_data = _load_extract_data(monkeypatch, "extract_data_module_f4")

    # SALARY: dạng USD và lương thương lượng.
    salaries = extract_data.extract_salary_entities("Lương $2,000 - $3,000 USD, lương thương lượng")
    salary_values = [s["entity"].lower() for s in salaries]
    assert any("$2,000 - $3,000 usd" in v for v in salary_values)
    assert any("lương thương lượng" in v for v in salary_values)


def test_extract_entities_ner_returns_empty_for_blank_text(monkeypatch):
    extract_data = _load_extract_data(monkeypatch, "extract_data_module_g1")

    assert extract_data.extract_entities_ner("") == []
    assert extract_data.extract_entities_ner("   ") == []


def test_extract_entities_ner_continues_when_a_chunk_fails(monkeypatch):
    extract_data = _load_extract_data(monkeypatch, "extract_data_module_g2")

    monkeypatch.setattr(extract_data, "_chunk_text_by_tokens", lambda *_a, **_k: ["ok", "bad"])

    def _ner(chunk):
        if chunk == "bad":
            raise RuntimeError("pipeline failed")
        return [{"word": "OpenAI", "entity_group": "ORG", "score": 0.91}]

    monkeypatch.setattr(extract_data, "ner_pipeline", _ner)
    out = extract_data.extract_entities_ner("OpenAI tuyển Data Engineer lương 30 triệu")
    labels = {e["label"] for e in out}
    assert "ORG" in labels
    assert "JOB_ROLE" in labels
    assert "SALARY" in labels


def test_group_entities_dedups_b_i_prefix(monkeypatch):
    extract_data = _load_extract_data(monkeypatch, "extract_data_module_h")

    grouped = extract_data.group_entities(
        [
            {"entity": "OpenAI", "label": "B-ORGANIZATION"},
            {"entity": "OpenAI", "label": "I-ORGANIZATION"},
            {"entity": "OpenAI", "label": "ORG"},
            {"entity": "Sam", "label": "B-PER"},
            {"entity": "Sam", "label": "I-PER"},
        ]
    )
    assert grouped["ORG"] == ["OpenAI"]
    assert grouped["PER"] == ["Sam"]


def test_ner_json_file_output_name_with_filtered_prefix(monkeypatch, tmp_path):
    extract_data = _load_extract_data(monkeypatch, "extract_data_module_h2")

    extract_data.EXTRACTED_DATA_DIR = str(tmp_path)
    monkeypatch.setattr(extract_data, "extract_entities_ner", lambda _text: [{"entity": "OpenAI", "label": "ORG", "score": 0.95}])

    payload = {
        "source_platform": "Demo",
        "post_detail": [{"title": "A", "content": "B", "is_relevant": True}],
    }

    with_prefix = tmp_path / "filtered_data_DT.json"
    with_prefix.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    out1 = extract_data.ner_json_file_phobert(str(with_prefix))
    assert Path(out1).name == "extracted_data_phobert_DT.json"


def test_ner_json_file_output_name_without_filtered_prefix(monkeypatch, tmp_path):
    extract_data = _load_extract_data(monkeypatch, "extract_data_module_h3")

    extract_data.EXTRACTED_DATA_DIR = str(tmp_path)
    monkeypatch.setattr(extract_data, "extract_entities_ner", lambda _text: [{"entity": "OpenAI", "label": "ORG", "score": 0.95}])

    payload = {
        "source_platform": "Demo",
        "post_detail": [{"title": "A", "content": "B", "is_relevant": True}],
    }

    no_prefix = tmp_path / "custom_input.json"
    no_prefix.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    out2 = extract_data.ner_json_file_phobert(str(no_prefix))
    assert Path(out2).name == "extracted_data_phobert_custom_input.json"
