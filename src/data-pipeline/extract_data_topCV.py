import json
import os
import sys

# Cấu hình thư mục
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILTERED_DATA_DIR = os.path.join(BASE_DIR, "filtered_data", "topCV")
EXTRACTED_DATA_DIR = os.path.join(BASE_DIR, "extracted_data", "topCV")

def extract_topcv(input_path: str) -> str:
    if not os.path.exists(input_path):
        print(f"[LỖI] Không tìm thấy file: {input_path}")
        return ""

    print(f"\n{'=' * 55}")
    print(f"Đang xử lý trích xuất TopCV: {os.path.basename(input_path)}")
    print(f"{'=' * 55}")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    posts = data.get("post_detail", [])
    relevant_posts = [p for p in posts if p.get("is_relevant") is True]

    print(f"Tổng số bài: {len(posts)} | Số bài hợp lệ (is_relevant=True): {len(relevant_posts)}")

    final_posts = []
    for post in relevant_posts:
        # Chuẩn hóa các trường
        org = post.get("ORG", "").strip()
        date = post.get("DEADLINE_DATE", "").strip()
        salary = post.get("SALARY", "").strip()
        job_role = post.get("JOB_ROLE", "").strip()
        
        entities = {
            "ORG": [org] if org else [],
            "LOC": post.get("LOC", []),
            "DEADLINE_DATE": [date] if date else [],
            "SALARY": [salary] if salary else [],
            "JOB_ROLE": [job_role] if job_role else [],
            "SKILL/TECH": post.get("SKILL/TECH", [])
        }

        title_raw = str(post.get("title", "")).strip()
        created_at_raw = str(post.get("created_at", "")).strip()

        # Lưu lại cấu trúc bài viết đã chuẩn hoá entities
        final_post = {
            "title": title_raw,
            "created_at": created_at_raw,
            "entities": entities
        }
        final_posts.append(final_post)

    data["post_detail"] = final_posts

    # Ghi ra file
    os.makedirs(EXTRACTED_DATA_DIR, exist_ok=True)
    
    # Giữ nguyên tên file (YYYY_MM_DD.json)
    output_path = os.path.join(EXTRACTED_DATA_DIR, os.path.basename(input_path))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Đã lưu {len(final_posts)} bài viết vào: {output_path}")
    return output_path

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Chuyển đổi dữ liệu TopCV sang format Entities")
    parser.add_argument(
        "files", nargs="*",
        help="Đường dẫn file filtered_data_*.json cần xử lý. Nếu bỏ trống, tự scan."
    )
    args = parser.parse_args()

    if args.files:
        json_files = [os.path.abspath(f) for f in args.files]
        for f in json_files:
            extract_topcv(f)
    else:
        # Tự scan thư mục filtered_data/topCV
        if os.path.isdir(FILTERED_DATA_DIR):
            for f in os.listdir(FILTERED_DATA_DIR):
                if f.endswith(".json"):
                    extract_topcv(os.path.join(FILTERED_DATA_DIR, f))
        else:
            print(f"[LỖI] Thư mục không tồn tại: {FILTERED_DATA_DIR}")

if __name__ == "__main__":
    main()
