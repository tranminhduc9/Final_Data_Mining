"""
==========================================================
  SCRIPT TRÍCH XUẤT THỰC THỂ (NER) - GROQ API (LLM)
  Chiến lược: Gọi Groq LLM để nhận dạng toàn bộ entities
==========================================================

PIPELINE:
  1. Đọc các file `filtered_data_*.json` (hoặc danh sách file được truyền vào)
     Cấu trúc file: { "source_platform", "source_url", "scraped_at",
                      "post_detail": [ { "title", "content", "is_relevant" } ] }
  2. Chỉ giữ lại các bài có `is_relevant = true`
  3. Gộp `title + content`, gửi lên Groq API (model llama-3.3-70b-versatile)
     để trích xuất 7 loại thực thể:
       - PER      : người / cá nhân
       - ORG      : tổ chức / công ty
       - LOC      : địa điểm / khu vực
       - DATE     : ngày tháng năm
       - TECH     : công nghệ / ngôn ngữ lập trình / framework / tool
       - JOB_ROLE : vị trí / chức danh nghề nghiệp
       - SALARY   : thông tin lương / mức lương
  4. Parse JSON response từ Groq, chuẩn hóa và lưu vào field `entities`
  5. Output file có tên: extracted_data_groq_*.json

Lưu ý:
- Script này dùng Groq API, cần biến môi trường GROQ_API_KEY
  hoặc truyền vào qua tham số --api-key.
- Thư viện bắt buộc: `groq`, `python-dotenv` (tùy chọn).
  Cài đặt: pip install groq python-dotenv
"""

import argparse
import json
import os
import re
import sys
import time
from typing import List, Optional

try:
    from groq import Groq
except ImportError:
    print("[LỖI] Chưa cài thư viện groq. Chạy: pip install groq")
    sys.exit(1)

# Hỗ trợ load .env nếu có python-dotenv
from dotenv import load_dotenv

# Load biến môi trường từ file .env cùng thư mục với script
_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=_ENV_PATH)


if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


# ==========================================
# CẤU HÌNH
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILTERED_DATA_DIR = os.path.join(BASE_DIR, "filtered_data")
EXTRACTED_DATA_DIR = os.path.join(BASE_DIR, "extracted_data")
DIRECTORY = FILTERED_DATA_DIR

# Model Groq sẽ dùng
GROQ_MODEL = "llama-3.3-70b-versatile"

# Số ký tự tối đa gửi lên LLM (tránh vượt context window)
MAX_TEXT_CHARS = 4000

# Số lần retry khi gặp lỗi API (rate limit, network...)
MAX_RETRIES = 3
RETRY_DELAY_SEC = 5  # giây chờ giữa mỗi lần retry


# ==========================================
# PROMPT TEMPLATE
# ==========================================

SYSTEM_PROMPT = """Bạn là một hệ thống trích xuất thực thể (Named Entity Recognition) chuyên nghiệp cho văn bản tiếng Việt về lĩnh vực IT / công nghệ thông tin.

Nhiệm vụ: Đọc đoạn văn bản (tiếng Việt hoặc tiếng Anh) và trích xuất các thực thể thuộc 7 nhóm sau:
- PER: Tên người, cá nhân (VD: Nguyễn Văn A, Elon Musk, Jensen Huang)
- ORG: Tổ chức, công ty, trường học, cơ quan (VD: FPT Software, Google, Đại học Bách Khoa)
- LOC: Địa điểm, quốc gia, tỉnh thành, khu vực (VD: Hà Nội, Việt Nam, Silicon Valley)
- DATE: Ngày tháng năm, khoảng thời gian (VD: ngày 12 tháng 3 năm 2024, Q1/2025, tháng 6/2024)
- TECH: Công nghệ, ngôn ngữ lập trình, framework, tool, nền tảng, AI model (VD: Python, React, Docker, ChatGPT, TensorFlow, AWS)
- JOB_ROLE: Vị trí, chức danh nghề nghiệp (VD: Software Engineer, Giám đốc công nghệ, Data Scientist, CEO)
- SALARY: Thông tin lương, mức lương, thu nhập (VD: 15 triệu VNĐ, $3,000 USD, lương thương lượng)

Quy tắc:
1. Mỗi thực thể có thể xuất hiện nhiều lần nhưng chỉ liệt kê MỘT LẦN duy nhất trong mỗi nhóm.
2. Chỉ trích xuất thực thể thực sự xuất hiện trong văn bản, KHÔNG được bịa đặt.
3. Trả về KẾT QUẢ DUY NHẤT là JSON hợp lệ, KHÔNG có bất kỳ văn bản giải thích nào khác.
4. Nếu một nhóm không có thực thể, trả về mảng rỗng [].

Định dạng JSON trả về (bắt buộc):
{
  "PER": ["tên người 1", "tên người 2"],
  "ORG": ["tổ chức 1", "tổ chức 2"],
  "LOC": ["địa điểm 1"],
  "DATE": ["ngày tháng 1"],
  "TECH": ["công nghệ 1", "công nghệ 2"],
  "JOB_ROLE": ["chức danh 1"],
  "SALARY": ["mức lương 1"]
}"""

USER_PROMPT_TEMPLATE = """Trích xuất thực thể từ đoạn văn bản sau:

---
{text}
---

Chỉ trả về JSON, không giải thích thêm."""


# ==========================================
# KHỞI TẠO GROQ CLIENT
# ==========================================

def create_groq_client(api_key: Optional[str] = None) -> Groq:
    """
    Khởi tạo Groq client với API key.
    Ưu tiên: tham số --api-key > biến API_KEY trong .env > biến GROQ_API_KEY.
    """
    key = (
        api_key
        or os.environ.get("API_KEY", "")
        or os.environ.get("GROQ_API_KEY", "")
    )
    if not key:
        print("[LỖI] Không tìm thấy API key.")
        print(f"  → File .env đang tìm tại: {_ENV_PATH}")
        print("  → Thêm dòng sau vào file .env:  API_KEY=<groq-key>")
        print("  → Hoặc truyền trực tiếp:         --api-key <groq-key>")
        sys.exit(1)
    return Groq(api_key=key)


# ==========================================
# HÀM GỌI GROQ API
# ==========================================

def call_groq_ner(client: Groq, text: str) -> dict:
    """
    Gửi text lên Groq API để trích xuất NER.
    Trả về dict có 7 key: PER, ORG, LOC, DATE, TECH, JOB_ROLE, SALARY.
    Mỗi key là list[str].
    Retry tối đa MAX_RETRIES lần nếu gặp lỗi.
    """
    empty_result = {
        "PER": [], "ORG": [], "LOC": [],
        "DATE": [], "TECH": [], "JOB_ROLE": [], "SALARY": []
    }

    # Cắt bớt nếu văn bản quá dài
    if len(text) > MAX_TEXT_CHARS:
        text = text[:MAX_TEXT_CHARS] + "..."

    user_prompt = USER_PROMPT_TEMPLATE.format(text=text)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_prompt},
                ],
                temperature=0.0,       # Deterministic output
                max_tokens=1024,
                response_format={"type": "json_object"},  # Yêu cầu JSON mode
            )

            raw_content = response.choices[0].message.content.strip()
            parsed = json.loads(raw_content)

            # Validate & chuẩn hóa: đảm bảo đủ 7 key, mỗi value là list[str]
            result = {}
            for key in ("PER", "ORG", "LOC", "DATE", "TECH", "JOB_ROLE", "SALARY"):
                val = parsed.get(key, [])
                if isinstance(val, list):
                    # Lọc giá trị rỗng và chuẩn hóa
                    result[key] = [
                        normalize_entity(str(v).strip(), key)
                        for v in val
                        if v and str(v).strip()
                    ]
                    # Bỏ giá trị rỗng sau normalize
                    result[key] = [v for v in result[key] if v]
                    # Dedup (giữ thứ tự)
                    seen = set()
                    deduped = []
                    for v in result[key]:
                        if v.lower() not in seen:
                            seen.add(v.lower())
                            deduped.append(v)
                    result[key] = deduped
                else:
                    result[key] = []

            return result

        except json.JSONDecodeError as e:
            print(f"    [WARN] Attempt {attempt}/{MAX_RETRIES} - JSON decode error: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SEC)
            else:
                print("    [WARN] Không parse được JSON từ Groq. Trả về rỗng.")
                return empty_result

        except Exception as e:
            err_str = str(e)
            # Rate limit → chờ lâu hơn
            if "rate_limit" in err_str.lower() or "429" in err_str:
                wait = RETRY_DELAY_SEC * attempt * 2
                print(f"    [WARN] Rate limit (attempt {attempt}/{MAX_RETRIES}). Chờ {wait}s...")
                time.sleep(wait)
            else:
                print(f"    [WARN] Attempt {attempt}/{MAX_RETRIES} - Lỗi Groq API: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SEC)
                else:
                    print("    [WARN] Vượt quá số lần retry. Trả về rỗng.")
                    return empty_result

    return empty_result


# ==========================================
# HÀM CHUẨN HÓA THỰC THỂ
# ==========================================

def normalize_entity(text: str, label: str = "") -> str:
    """
    Chuẩn hóa chuỗi entity trước khi lưu:
      - Bỏ khoảng trắng thừa đầu/cuối và thu gọn khoảng trắng bên trong.
      - Xóa ký tự ▁ (artifact subword của SentencePiece).
      - Xóa các ký tự đặc biệt lẻ ở đầu/cuối.
      - Với PER: title-case nếu toàn bộ chuỗi là chữ thường.
    Trả về chuỗi đã chuẩn hóa.
    """
    if not text:
        return ""

    text = text.replace("▁", "").replace("\u2581", "")
    text = " ".join(text.split())
    text = text.strip(".,;:\"'()[]{}…")
    text = text.strip()

    if label.upper() == "PER" and text and text == text.lower():
        text = text.title()

    return text


# ==========================================
# HÀM XỬ LÝ FILE JSON
# ==========================================

def ner_json_file_groq(input_path: str, client: Groq) -> str:
    print(f"\n{'=' * 55}")
    print(f"[Groq NER] Đang xử lý: {os.path.basename(input_path)}")
    print(f"{'=' * 55}")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    posts = data.get("post_detail", [])
    total = len(posts)
    relevant_indices = [i for i, p in enumerate(posts) if p.get("is_relevant") is True]

    print(
        f"Tổng: {total} bài | Chỉ xử lý & ghi ra: {len(relevant_indices)} | "
        f"Bỏ qua (is_relevant=false): {total - len(relevant_indices)}"
    )

    relevant_posts = [posts[i] for i in relevant_indices]

    print(f"\n[Bước] Gọi Groq API ({GROQ_MODEL}) để trích xuất entities...")
    all_entities: List[dict] = []

    for i, post in enumerate(relevant_posts):
        text = f"{post.get('title', '')}. {post.get('content', '')}".strip()
        title_preview = post.get("title", "")[:45]

        print(f"  [{relevant_indices[i] + 1}/{total}] {title_preview}")

        entities = call_groq_ner(client, text)
        all_entities.append(entities)

        # Log tóm tắt
        summary = " | ".join(
            f"{k[:3].upper()}:{len(v)}" for k, v in entities.items() if v
        ) or "—"
        print(f"       ENTITIES: {summary}")

        # Nghỉ nhỏ giữa các request để tránh rate limit
        time.sleep(0.3)

    # Gán entities vào từng bài relevant
    for i, idx in enumerate(relevant_indices):
        posts[idx]["entities"] = all_entities[i]

    # Output chỉ giữ lại bài is_relevant=true
    output_posts = [posts[i] for i in relevant_indices]
    data_out = {k: v for k, v in data.items() if k != "post_detail"}
    data_out["post_detail"] = output_posts

    # Lưu output
    os.makedirs(EXTRACTED_DATA_DIR, exist_ok=True)
    base_name = os.path.basename(input_path)

    if base_name.startswith("filtered_data_"):
        suffix = base_name[len("filtered_data_"):]
    else:
        suffix = base_name

    output_filename = "extracted_data_groq_" + suffix
    output_path = os.path.join(EXTRACTED_DATA_DIR, output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data_out, f, ensure_ascii=False, indent=2)

    print(f"\n  → Kết quả: {output_path} (chỉ {len(output_posts)} bài is_relevant=true)")
    return output_path


# ==========================================
# HÀM CHÍNH
# ==========================================

def main():
    global DIRECTORY, GROQ_MODEL

    parser = argparse.ArgumentParser(
        description=(
            "NER trích xuất entity cho bài IT bằng Groq API (LLM). "
            "Nhận dạng 7 loại thực thể: PER, ORG, LOC, DATE, TECH, JOB_ROLE, SALARY."
        )
    )
    parser.add_argument(
        "files",
        nargs="*",
        help=(
            "Đường dẫn file filtered_data_*.json cần xử lý. "
            "Nếu bỏ trống, script sẽ tự scan thư mục mặc định hoặc --dir."
        ),
    )
    parser.add_argument(
        "--dir",
        dest="directory",
        default=DIRECTORY,
        help=f"Thư mục chứa file filtered_data_*.json (mặc định: {DIRECTORY}).",
    )
    parser.add_argument(
        "--api-key",
        dest="api_key",
        default=None,
        help=(
            "Groq API key. Nếu không truyền, script sẽ dùng biến môi trường API_KEY."
        ),
    )
    parser.add_argument(
        "--model",
        dest="model",
        default=GROQ_MODEL,
        help=f"Tên model Groq sẽ dùng (mặc định: {GROQ_MODEL}).",
    )
    args = parser.parse_args()

    DIRECTORY = args.directory
    GROQ_MODEL = args.model

    # Khởi tạo Groq client
    client = create_groq_client(api_key=args.api_key)

    if args.files:
        labeled_files = [os.path.abspath(f) for f in args.files]
        missing = [f for f in labeled_files if not os.path.exists(f)]
        if missing:
            for f in missing:
                print(f"[LỖI] Không tìm thấy file: {f}")
            sys.exit(1)
    else:
        if not os.path.isdir(DIRECTORY):
            print(f"[LỖI] Thư mục không tồn tại: {DIRECTORY}")
            sys.exit(1)

        labeled_files = [
            os.path.join(DIRECTORY, f)
            for f in os.listdir(DIRECTORY)
            if f.startswith("filtered_data_") and f.endswith(".json")
        ]

    if not labeled_files:
        print("Không tìm thấy file đầu vào.")
        return

    print(f"[INFO] Dùng model Groq: {GROQ_MODEL}")
    print(f"Tìm thấy {len(labeled_files)} file:")
    for f in labeled_files:
        print(f"  - {os.path.basename(f)}")

    for file_path in labeled_files:
        ner_json_file_groq(file_path, client)

    print(f"\n{'=' * 55}")
    print(
        "Hoàn thành! Kiểm tra các file extracted_data_groq_*.json "
        "trong thư mục extracted_data"
    )
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
