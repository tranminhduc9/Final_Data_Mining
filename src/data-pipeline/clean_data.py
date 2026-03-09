import argparse
import json
import re
import os
import sys
from datetime import datetime

# Fix encoding cho Windows terminal
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ==========================================
# CẤU HÌNH - Thay đổi ở đây nếu cần
# ==========================================
# Thư mục gốc của project (dựa trên vị trí file hiện tại)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Thư mục chứa dữ liệu thô và dữ liệu đã làm sạch (dạng tương đối, an toàn khi đưa lên GitHub)
RAW_DATA_DIR = os.path.join(BASE_DIR, "raw_data")
CLEANED_DATA_DIR = os.path.join(BASE_DIR, "cleaned_data")

# Map tên thứ tiếng Việt -> số thứ tự (dùng khi format lại)
THU_MAP = {
    "thứ hai": "Thứ Hai",
    "thứ ba": "Thứ Ba",
    "thứ tư": "Thứ Tư",
    "thứ năm": "Thứ Năm",
    "thứ sáu": "Thứ Sáu",
    "thứ bảy": "Thứ Bảy",
    "chủ nhật": "Chủ Nhật",
}

# ==========================================
# HÀM LÀM SẠCH VĂN BẢN
# ==========================================

def clean_text(text: str) -> str:
    """
    Xoá icon, emoji, ký hiệu đặc biệt và chuẩn hoá khoảng trắng.
    Giữ lại: chữ cái, số, dấu câu tiếng Việt, các ký hiệu phổ biến (%, $, /)
    """
    if not text:
        return ""

    # Xoá emoji và các ký hiệu Unicode đặc biệt (ranges phổ biến)
    text = re.sub(
        r"[\U0001F600-\U0001F64F"   # Emoticons
        r"\U0001F300-\U0001F5FF"    # Symbols & Pictographs
        r"\U0001F680-\U0001F6FF"    # Transport & Map
        r"\U0001F1E0-\U0001F1FF"    # Flags
        r"\U00002600-\U000027BF"    # Misc Symbols
        r"\U0001F900-\U0001F9FF"    # Supplemental Symbols
        r"\U00002702-\U000027B0"    # Dingbats
        r"\U000024C2-\U0001F251"    # Enclosed chars
        r"]+",
        "", text
    )

    # Chuẩn hoá dấu ngoặc kép kiểu curly -> thẳng
    text = text.replace("\u201c", '"').replace("\u201d", '"')  # " "
    text = text.replace("\u2018", "'").replace("\u2019", "'")  # ' '
    text = text.replace("\u201e", '"').replace("\u201f", '"')  # „ ‟
    text = text.replace("\u00ab", '"').replace("\u00bb", '"')  # « »

    # Xoá ký tự điều khiển (trừ newline thông thường)
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)

    # Chuẩn hoá khoảng trắng thừa
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()

    return text


def clean_title(title: str) -> str:
    """Làm sạch trường title."""
    return clean_text(title)


def clean_description(description: str) -> str:
    """
    Làm sạch trường description:
    - Xoá số bình luận cuối chuỗi (dạng ' 23', ' 128' ...)
    - Xử lý địa danh viết liền với tên riêng (VD: 'MỸCharlie' -> 'Charles')
    - Xoá icon, ký tự đặc biệt
    """
    if not description:
        return ""

    text = clean_text(description)

    # Xoá số bình luận cuối chuỗi: khoảng trắng + 1-3 chữ số ở cuối
    # VD: "...hàng triệu người. 63" -> "...hàng triệu người."
    text = re.sub(r"\s+\d{1,3}\s*$", "", text)

    # Xử lý địa danh VIẾT HOA liền với chữ thường
    # VD: "MỸCharlie" -> "Mỹ - Charlie" | "HÀ NỘINhiều" -> "Hà Nội - Nhiều"
    # Pattern: chuỗi CHỮ HOA (có dấu) + chữ thường đầu tiên của từ tiếp theo
    text = re.sub(
        r"([A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴ]{2,})"
        r"([A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴ][a-záàảãạăắằẳẵặâấầẩẫậđéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ])",
        lambda m: m.group(1).capitalize() + " - " + m.group(2),
        text
    )

    text = text.strip()
    return text


# ==========================================
# HÀM CHUẨN HOÁ NGÀY GIỜ
# ==========================================

def normalize_datetime(created_at: str) -> str:
    """
    Chuẩn hoá created_at từ nhiều format khác nhau về:
    'Thứ Hai, 02/03/2026, 15:58'

    Hỗ trợ các format đầu vào:
    - VnExpress: "Thứ sáu, 6/3/2026, 07:00 (GMT+7)"
    - Dân Trí:   "Thứ sáu, 06/03/2026 - 15:58"
    """
    if not created_at or not created_at.strip():
        return ""

    text = created_at.strip()

    # Xoá phần múi giờ: "(GMT+7)", "(GMT+0)", v.v.
    text = re.sub(r"\s*\(GMT[+-]\d+\)\s*", "", text)
    text = text.strip()

    # --- Format 1: VnExpress "Thứ sáu, 6/3/2026, 07:00" ---
    match_vn = re.match(
        r"(Thứ\s+\w+|Chủ\s+nhật),\s*(\d{1,2})/(\d{1,2})/(\d{4}),\s*(\d{2}:\d{2})",
        text, re.IGNORECASE
    )

    # --- Format 2: Dân Trí "Thứ sáu, 06/03/2026 - 15:58" ---
    match_dt = re.match(
        r"(Thứ\s+\w+|Chủ\s+nhật),\s*(\d{2})/(\d{2})/(\d{4})\s+-\s*(\d{2}:\d{2})",
        text, re.IGNORECASE
    )

    if match_vn:
        thu_raw, day, month, year, time = match_vn.groups()
    elif match_dt:
        thu_raw, day, month, year, time = match_dt.groups()
    else:
        # Không nhận dạng được, trả về clean cơ bản
        return clean_text(created_at)

    # Chuẩn hoá tên thứ (viết hoa chữ đầu)
    thu_lower = thu_raw.lower().strip()
    thu_chuan = THU_MAP.get(thu_lower, thu_raw.title())

    # Đảm bảo ngày tháng có 2 chữ số
    day_fmt   = day.zfill(2)
    month_fmt = month.zfill(2)

    return f"{thu_chuan}, {day_fmt}/{month_fmt}/{year}, {time}"


# ==========================================
# HÀM CHÍNH
# ==========================================

def clean_json_file(input_path: str) -> str:
    """
    Đọc file JSON, làm sạch và chuẩn hoá dữ liệu,
    ghi ra file mới với tiền tố 'cleaned_'.
    Trả về đường dẫn file output.
    """
    print(f"\n{'='*50}")
    print(f"Đang xử lý: {os.path.basename(input_path)}")
    print(f"{'='*50}")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    posts = data.get("post_detail", [])
    total = len(posts)
    cleaned_count = 0

    for i, post in enumerate(posts):
        original = dict(post)

        post["title"]       = clean_title(post.get("title", ""))
        post["description"] = clean_description(post.get("description", ""))
        post["created_at"]  = normalize_datetime(post.get("created_at", ""))

        # Báo cáo nếu có thay đổi (rút gọn output, chỉ in tiêu đề và mô tả)
        if post != original:
            cleaned_count += 1
            print(f"\n  Bài {i+1}: '{post['title'][:50]}...'")
            if post["description"] != original.get("description", ""):
                print(f"    description: {repr(original['description'][-40:])}")
                print(f"             -> {repr(post['description'][-40:])}")

    # Lưu file output vào thư mục cleaned_data với tên dạng cleaned_data_*.json
    os.makedirs(CLEANED_DATA_DIR, exist_ok=True)
    base_name = os.path.basename(input_path)

    # Nếu file đầu vào có dạng raw_data_XXX.json -> cleaned_data_XXX.json
    if base_name.startswith("raw_data_"):
        suffix = base_name[len("raw_data_"):]  # phần XXX.json
    else:
        # Nếu không đúng pattern, dùng nguyên tên làm suffix
        suffix = base_name

    output_filename = "cleaned_data_" + suffix
    output_path = os.path.join(CLEANED_DATA_DIR, output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n  [OK] Đã làm sạch {cleaned_count}/{total} bài viết")
    print(f"  [OK] Đã lưu vào: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Làm sạch và chuẩn hoá dữ liệu JSON")
    parser.add_argument(
        "files", nargs="*",
        help="Đường dẫn file data_*.json cần xử lý. "
             "Nếu bỏ trống, tự scan thư mục DIRECTORY."
    )
    args = parser.parse_args()

    if args.files:
        json_files = [os.path.abspath(f) for f in args.files]
        missing = [f for f in json_files if not os.path.exists(f)]
        if missing:
            for f in missing:
                print(f"[LỖI] Không tìm thấy file: {f}")
            sys.exit(1)
    else:
        # Nếu không chỉ định file, tự scan thư mục raw_data trong project
        if os.path.isdir(RAW_DATA_DIR):
            json_files = [
                os.path.join(RAW_DATA_DIR, f)
                for f in os.listdir(RAW_DATA_DIR)
                if f.startswith("raw_data_") and f.endswith(".json")
            ]
        else:
            json_files = []

    if not json_files:
        print(f"Không tìm thấy file đầu vào.")
        return

    print(f"Tìm thấy {len(json_files)} file cần xử lý:")
    for f in json_files:
        print(f"  - {os.path.basename(f)}")

    for file_path in json_files:
        clean_json_file(file_path)

    print(f"\n{'='*50}")
    print("Hoàn thành! Tất cả file đã được làm sạch.")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
