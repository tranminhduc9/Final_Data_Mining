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


clean_data = _load_module("clean_data_module", "src/data-pipeline/clean_data.py")


def test_clean_text_and_datetime_scenario_matrix():
    text_cases = [
        ('  “AI”\tla\u0300  tuy\u1ec7t v\u1eddi 😀\x07  ', '"AI" la\u0300 tuy\u1ec7t v\u1eddi'),
        (None, ""),
        ("", ""),
    ]

    for raw, expected in text_cases:
        assert clean_data.clean_text(raw) == expected

    dt_cases = [
        ("Th\u1ee9 s\u00e1u, 6/3/2026, 07:00 (GMT+7)", "06/03/2026"),
        ("Th\u1ee9 s\u00e1u, 06/03/2026 - 15:58", "06/03/2026"),
        ("  Ch\u1ee7 nh\u1eadt, 9/3/2026, 09:30 (GMT+0)  ", "09/03/2026"),
        ("2/3/2026", "02/03/2026"),
        ("Ngay khong hop le", "Ngay khong hop le"),
    ]

    for raw, expected in dt_cases:
        assert clean_data.normalize_datetime(raw) == expected


def test_clean_description_and_skilltech_scenario_matrix():
    description = "M\u1ef8Charlie c\u00f4ng b\u1ed1 m\u1ea3nh gh\u00e9p AI. 63"
    cleaned_description = clean_data.clean_description(description)
    assert cleaned_description.endswith("AI.")
    assert "M\u1ef9 - Charlie" in cleaned_description

    assert clean_data.clean_skill_tech(["Python", "Xem th\u00eam", "Python", "FastAPI", "python"]) == [
        "Python",
        "FastAPI",
        "python",
    ]
    assert clean_data.clean_skill_tech("Python, FastAPI") == "Python, FastAPI"


def test_clean_json_file_large_mixed_pipeline_case(tmp_path):
    input_data = {
        "source_platform": "MixedSource",
        "post_detail": [
            {
                "title": "😀 Vi\u1ec7c l\u00e0m AI",
                "description": "M\u00f4 t\u1ea3 b\u00e0i vi\u1ebft 12",
                "created_at": "2/3/2026",
            },
            {
                "JOB_ROLE": "  Backend Developer  ",
                "DEADLINE_DATE": "2/3/2026",
                "SKILL/TECH": ["Python", "Xem th\u00eam", "Python"],
                "title": "  Tin tuy\u1ec3n d\u1ee5ng 😀  ",
                "description": "M\u00f4 t\u1ea3 123",
            },
        ],
    }

    non_raw_input = tmp_path / "input_custom.json"
    raw_input = tmp_path / "raw_data_topCV.json"

    non_raw_input.write_text(json.dumps(input_data, ensure_ascii=False), encoding="utf-8")
    raw_input.write_text(json.dumps(input_data, ensure_ascii=False), encoding="utf-8")

    clean_data.CLEANED_DATA_DIR = str(tmp_path / "cleaned_data")

    non_raw_out = clean_data.clean_json_file(str(non_raw_input))
    raw_out = clean_data.clean_json_file(str(raw_input))

    assert Path(non_raw_out).name == "cleaned_data_input_custom.json"
    assert Path(raw_out).name == "cleaned_data_topCV.json"

    non_raw_payload = json.loads(Path(non_raw_out).read_text(encoding="utf-8"))
    raw_payload = json.loads(Path(raw_out).read_text(encoding="utf-8"))

    assert non_raw_payload["post_detail"][0]["title"] == "Vi\u1ec7c l\u00e0m AI"
    assert non_raw_payload["post_detail"][0]["created_at"] == "02/03/2026"

    assert raw_payload["post_detail"][1]["JOB_ROLE"] == "Backend Developer"
    assert raw_payload["post_detail"][1]["DEADLINE_DATE"] == "02/03/2026"
    assert raw_payload["post_detail"][1]["SKILL/TECH"] == ["Python"]


def test_clean_edge_cases_quotes_whitespace_and_unchanged_posts(tmp_path):
    # --- curly quotes → straight quotes ---
    assert clean_data.clean_text("\u201cHello\u201d \u2018world\u2019") == '"Hello" \'world\''
    assert clean_data.clean_text("\u00abGuillemets\u00bb") == '"Guillemets"'

    # --- whitespace-only → empty ---
    assert clean_data.clean_text("   \t  ") == ""

    # --- description without trailing number keeps text intact ---
    desc = clean_data.clean_description("M\u00f4 t\u1ea3 b\u00ecnh th\u01b0\u1eddng.")
    assert desc == "M\u00f4 t\u1ea3 b\u00ecnh th\u01b0\u1eddng."

    # --- empty / whitespace datetime ---
    assert clean_data.normalize_datetime("") == ""
    assert clean_data.normalize_datetime("   ") == ""
    assert clean_data.normalize_datetime(None) == ""

    # --- clean_json_file where nothing changes → output still created ---
    already_clean = {
        "source_platform": "TestSrc",
        "post_detail": [
            {"title": "Already clean", "description": "No emoji here", "created_at": "02/03/2026"},
        ],
    }
    in_file = tmp_path / "raw_data_clean.json"
    in_file.write_text(json.dumps(already_clean, ensure_ascii=False), encoding="utf-8")
    clean_data.CLEANED_DATA_DIR = str(tmp_path / "out")

    out_path = clean_data.clean_json_file(str(in_file))
    out_data = json.loads(Path(out_path).read_text(encoding="utf-8"))

    assert out_data["post_detail"][0]["title"] == "Already clean"
    assert out_data["post_detail"][0]["created_at"] == "02/03/2026"
