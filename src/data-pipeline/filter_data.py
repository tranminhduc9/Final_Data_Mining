"""
==========================================================
  NÂNG CẤP LÊN ASYNC (khi data đủ lớn, ~500+ bài)
==========================================================
Khi cần, chỉ cần:
  1. Đổi hàm classify_batch() → async, dùng generate_content_async()
  2. Đổi hàm filter_json_file() → async
  3. Thêm asyncio.Semaphore(MAX_CONCURRENT) để giới hạn concurrent
  4. Chạy bằng asyncio.run(main())
  → Phần còn lại của code không cần thay đổi
"""

import argparse
import json
import os
import sys
import time
from dotenv import load_dotenv

# Fix encoding cho Windows terminal
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

# ==========================================
# CẤU HÌNH - Chỉnh sửa tại đây
# ==========================================

API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")    # Dán API Key hoặc đặt GEMINI_API_KEY

# Thư mục gốc project (dựa trên vị trí file hiện tại)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Thư mục chứa file cleaned_data_*.json (output từ bước clean)
CLEANED_DATA_DIR = os.path.join(BASE_DIR, "cleaned_data")

# Thư mục chứa file filtered_data_*.json (output sau khi lọc IT)
FILTERED_DATA_DIR = os.path.join(BASE_DIR, "filtered_data")

# Thư mục mặc định để scan input (có thể override bằng --dir)
DIRECTORY  = CLEANED_DATA_DIR

MODEL      = "gemini-2.5-flash"
BATCH_SIZE = 10      # Số title gửi mỗi lần gọi API
DELAY      = 10.0    # Giây chờ giữa các batch (tránh rate limit)

# Khi nâng cấp async, thêm:
# MAX_CONCURRENT = 5                                    # Số batch chạy song song tối đa

# ==========================================
# KIỂM TRA CẤU HÌNH
# ==========================================

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("=" * 55)
    print("  LỖI: Chưa cài thư viện google-genai!")
    print("=" * 55)
    sys.exit(1)

# Khởi tạo Gemini
client = genai.Client(api_key=API_KEY)


# ==========================================
# HÀM PHÂN LOẠI THEO BATCH (Title-only)
# ==========================================

SYSTEM_PROMPT = """You are a binary classifier for Vietnamese IT news article titles.
For each title, output YES if the article is PRIMARILY about one of:
  1. AI / Machine Learning / LLM / Generative AI
  2. Software, apps, platforms, digital services, cloud
  3. Programming, dev tools, frameworks, open-source
  4. Cybersecurity (network attacks, malware, data breach, security software)
  5. Company news ONLY when the focus is a specific software/AI product or IT hiring/skills

Output NO if the article is primarily about:
  - Hardware specs/reviews/price (phones, laptops, TVs, peripherals)
  - Telecommunications infrastructure (5G/6G towers, spectrum, data plans)
  - Home appliances, vehicles, construction
  - Finance/stock/M&A without software/AI/IT hiring focus
  - Sports, entertainment, fashion, health, politics, environment

RULES:
- Hardware article containing AI chip → NO
- Company revenue/stock news → NO; software product or IT staff news → YES
- AI policy / digital transformation laws → YES
- When ambiguous, choose NO

INPUT: numbered list of titles
OUTPUT: same numbered list with YES or NO only, no extra text."""

# ==========================================
# KEYWORD PRE-FILTER (không tốn API quota)
# ==========================================

# Bài chứa từ khoá này → chắc chắn LIÊN QUAN → True ngay
WHITELIST = [
    # AI & mô hình ngôn ngữ
    r"\bAI\b", r"\bLLM\b", r"\bGPT\b", r"\bGenAI\b",
    "chatbot", "trí tuệ nhân tạo", "machine learning", "deep learning",
    "mô hình ngôn ngữ", "AI tạo sinh", "generative AI", "học máy",
    "tác nhân AI", "ảo giác AI", "mô hình AI", "neural network",
    "OpenAI", "Anthropic", "Mistral", "Llama", "Grok", "Gemini",
    "Claude", "Copilot", "ChatGPT", "Perplexity", "DeepSeek", "VinAI",
    # Phần mềm & nền tảng
    "phần mềm", "ứng dụng", "lập trình", "mã nguồn",
    "open-source", "hệ điều hành", "framework", "database",
    r"\bAPI\b", r"\bSaaS\b", r"\bPaaS\b", r"\bIaaS\b",
    "microservice", "DevOps", "CI/CD", "web app", "mobile app",
    "backend", "frontend", "full-stack", "fullstack",
    # Ngôn ngữ & công cụ lập trình
    "Python", "JavaScript", "TypeScript", "Golang", "Kotlin",
    r"\bJava\b", r"\bRust\b",
    "React", "Vue", "Angular", "Node.js", "NextJS", "NestJS",
    "Spring Boot", "Django", "FastAPI", "Flutter",
    r"\bGitHub\b", "Docker", "Kubernetes", r"\bLinux\b",
    r"\bWindows\b", r"\bAndroid\b", r"\biOS\b",
    # Cloud & data
    r"\bAWS\b", "Azure", r"\bGCP\b", "Google Cloud", "Oracle Cloud",
    "dữ liệu", "big data", "trung tâm dữ liệu", "data center",
    "data warehouse", "data lake", "Spark", "Kafka", "Airflow",
    # Bảo mật
    "bảo mật", "an ninh mạng", "malware", "ransomware",
    "tấn công mạng", "DDoS", "rò rỉ dữ liệu", "lỗ hổng bảo mật",
    "mã độc", "phần mềm độc hại", "lừa đảo trực tuyến",
    r"\bVPN\b", "mã hóa", "xác thực", "firewall", "hacker",
    # Công ty & dịch vụ số
    "Microsoft", "Google", "Meta", "Samsung",
    "Netflix", "Spotify", "TikTok", "YouTube",
    "Zalo", "VNG", "FPT Software", "Viettel", "VNPT", "Momo",
    "thương mại điện tử", "thanh toán điện tử", "ngân hàng số",
    "ví điện tử", "mobile banking", "super app",
    # Luật & chính sách số
    "Luật Trí tuệ nhân tạo", "luật AI", "quản lý AI", "chuyển đổi số",
    "kinh tế số", "an toàn thông tin",
    # Tuyển dụng IT
    "tuyển dụng IT", "kỹ sư phần mềm", "lập trình viên",
    "data engineer", "data scientist", "ML engineer", "DevOps engineer",
]

# Bài chứa từ khoá này → chắc chắn KHÔNG LIÊN QUAN → False ngay
BLACKLIST = [
    # Thiên văn & không gian
    "nguyệt thực", "nhật thực", "hành tinh", "Mặt Trăng", "sao chổi",
    "thiên văn", "vũ trụ", "trăng máu", "diễu hành hành tinh",
    "sao Hỏa", "sao Kim", "Trái Đất", "hệ Mặt Trời",
    # Thiết bị gia dụng
    "máy hút ẩm", "điều hòa", "tủ lạnh", "máy giặt", "lò vi sóng",
    "máy lọc không khí", "máy hút bụi", "nồi cơm điện", "bếp điện",
    "máy nước nóng", "quạt điện", "bóng đèn",
    # Giao thông & xây dựng
    "xăng", "giao thông", "ổ gà", "tai nạn", "ô tô điện", "xe điện",
    "cầu đường", "cầu vượt", "hạ tầng giao thông",
    # Thể thao
    "bóng đá", "thể thao", "World Cup", "V-League", "AFF Cup",
    "bệnh viện", "thuốc", "vắc xin", "dịch bệnh", "ung thư",
    "vi rút", "bác sĩ", "sức khỏe",
    # Nông nghiệp & thực phẩm
    "nông nghiệp", "lúa gạo", "thực phẩm", "nhà hàng",
    "thủy sản", "chăn nuôi",
    # Tài chính thuần túy
    "bất động sản", "cho vay", "lãi suất ngân hàng", "trái phiếu",
    "vàng miếng", "bầu cử",
]
WHITELIST_L = WHITELIST   # giữ nguyên (đã có regex lẫn plain string)
BLACKLIST_L = [kw.lower() for kw in BLACKLIST]




import re as _re

# Tạo compiled regex cho từng keyword whitelist một lần duy nhất
# Các phần tử bắt đầu bằng r"\b" là regex, còn lại là plain string
_WL_REGEXES = []
for _kw in WHITELIST_L:
    if _kw.startswith(r"\b") or _kw.startswith("(?i)"):
        _WL_REGEXES.append(_re.compile(_kw, _re.IGNORECASE))
    else:
        _WL_REGEXES.append(None)  # plain string, dùng `in` bình thường


def keyword_filter(title: str):
    """
    Kiểm tra nhanh bằng từ khoá trước khi gọi API.
    Returns:
        True   → chắc chắn liên quan, bỏ qua API
        False  → chắc chắn không liên quan, bỏ qua API
        None   → không chắc, cần gọi API
    """
    t = title.lower()
    # BLACKLIST: plain substring match đủ (các từ dài, ít nhập nhằng)
    for kw in BLACKLIST_L:
        if kw in t:
            return False
    # WHITELIST: dùng regex cho từ ngắn/viết tắt, plain string cho cụm dài
    for kw_orig, regex in zip(WHITELIST_L, _WL_REGEXES):
        if regex is not None:
            if regex.search(title):   # search trên title gốc (giữ case cho regex \b)
                return True
        else:
            if kw_orig in t:
                return True
    return None  # Không chắc → để API quyết định


def classify_batch(titles: list[str]) -> list[bool]:
    """
    Gửi một batch titles lên Gemini, nhận về list kết quả True/False.
    Tự retry tối đa MAX_RETRIES lần nếu gặp lỗi 429 (rate limit).

    [Thiết kế để nâng cấp async]
    Khi nâng cấp: dùng await client.aio.models.generate_content()
    Phần còn lại của hàm giữ nguyên.
    """
    MAX_RETRIES = 3
    BASE_DELAY  = 10  # giây, nhân đôi mỗi lần retry

    title_list = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(titles))
    prompt = f"{SYSTEM_PROMPT}\n\nDanh sách tiêu đề:\n{title_list}"

    for attempt in range(MAX_RETRIES):
        try:
            # [Async upgrade] → await client.aio.models.generate_content()
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )
            raw_text = response.text or ""
            raw = raw_text.strip()

            if not raw:
                print("    [WARN] API không trả về nội dung — gán False cho toàn bộ batch này")
                return [False] * len(titles)

            # Parse kết quả: "1. YES\n2. NO\n3. YES" → [True, False, True]
            results = []
            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                parts = line.split(".", 1)
                answer = parts[-1].strip().upper() if len(parts) > 1 else parts[0].strip().upper()
                results.append(answer.startswith("YES"))

            if len(results) != len(titles):
                print(f"    [WARN] Parse lệch ({len(results)} vs {len(titles)}) — gán False cho toàn bộ batch này")
                return [False] * len(titles)

            return results

        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower():
                wait = BASE_DELAY * (2 ** attempt)  # 10s, 20s, 40s, 80s, 160s
                print(f"    [RATE LIMIT] Lần {attempt + 1}/{MAX_RETRIES} — chờ {wait}s rồi thử lại...")
                time.sleep(wait)
            else:
                print(f"    [WARN] Lỗi API: {e} — gán False cho toàn bộ batch này")
                return [False] * len(titles)

    print(f"    [ERROR] Đã thử {MAX_RETRIES} lần vẫn lỗi — gán False cho toàn bộ batch này")
    return [False] * len(titles)


def make_batches(lst: list, size: int) -> list[list]:
    """Chia list thành các batch có kích thước cố định."""
    return [lst[i:i + size] for i in range(0, len(lst), size)]


# ==========================================
# HÀM XỬ LÝ FILE JSON
# ==========================================

def _resolve_output_path(input_path: str) -> str:
    """Chuyển đường dẫn cleaned_*.json → đường dẫn filtered_data_*.json."""
    base = os.path.basename(input_path)
    for prefix in ("cleaned_data_", "cleaned_"):
        if base.startswith(prefix):
            suffix = base[len(prefix):]
            break
    else:
        suffix = base
    os.makedirs(FILTERED_DATA_DIR, exist_ok=True)
    return os.path.join(FILTERED_DATA_DIR, "filtered_data_" + suffix)


def _run_api_filter(posts: list, need_api: list, results_map: dict) -> None:
    """Gọi Gemini API cho các bài chưa được phân loại bằng keyword, cập nhật results_map."""
    ambiguous_titles = [posts[i].get("title") or posts[i].get("JOB_ROLE", "") for i in need_api]
    total_batches = -(-len(ambiguous_titles) // BATCH_SIZE)
    print(f"  Gọi API cho {len(ambiguous_titles)} bài → {total_batches} batch...")

    api_results: list = []
    for batch_idx, batch in enumerate(make_batches(ambiguous_titles, BATCH_SIZE)):
        start = batch_idx * BATCH_SIZE
        print(f"\n  Batch {batch_idx + 1}/{total_batches} (bài {start + 1}–{start + len(batch)})...")
        r = classify_batch(batch)
        api_results.extend(r)
        for j, (title, is_it) in enumerate(zip(batch, r)):
            mark = "✓" if is_it else "✗"
            print(f"    [{need_api[start + j] + 1}] {mark} {title[:55]}")
        if batch_idx < total_batches - 1:
            time.sleep(DELAY)

    for i, idx in enumerate(need_api):
        results_map[idx] = api_results[i]


def _remove_invalid_topcv_posts(posts: list[dict]) -> list[dict]:
    """
    (Dành riêng cho dữ liệu TopCV)
    Xoá bỏ hoàn toàn các bài tuyển dụng bị thiếu trường ORG hoặc DEADLINE_DATE.
    """
    valid_posts = []
    for p in posts:
        org = str(p.get("ORG", "")).strip()
        date = str(p.get("DEADLINE_DATE", "")).strip()
        if org and date:
            valid_posts.append(p)
    return valid_posts


def filter_json_file(input_path: str) -> str:
    """
    Đọc file cleaned JSON, gán nhãn is_relevant cho mỗi bài bằng batch API,
    ghi ra file filtered_data_*.json trong thư mục filtered_data.
    """
    print(f"\n{'=' * 55}")
    print(f"Đang xử lý: {os.path.basename(input_path)}")
    print(f"{'=' * 55}")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    posts = data.get("post_detail", [])
    
    # Dành riêng cho dữ liệu dạng TopCV -> xoá bài lỗi ORG/DEADLINE_DATE
    base_name = os.path.basename(input_path)
    if "topcv" in base_name.lower():
        original_len = len(posts)
        posts = _remove_invalid_topcv_posts(posts)
        if len(posts) < original_len:
            print(f"[TopCV] Đã xoá {original_len - len(posts)} bài thiếu ORG/DEADLINE_DATE.")

    print(f"Tổng số bài cần phân loại: {len(posts)}")

    # Bước 1: Keyword pre-filter
    pre_true, pre_false, need_api = [], [], []
    for i, post in enumerate(posts):
        title = post.get("title") or post.get("JOB_ROLE", "")
        result = keyword_filter(title)
        if result is True:    pre_true.append(i)
        elif result is False: pre_false.append(i)
        else:                 need_api.append(i)
    print(f"  Keyword: {len(pre_true)} ✓ | {len(pre_false)} ✗ | {len(need_api)} cần API")

    results_map = {i: True for i in pre_true}
    results_map.update({i: False for i in pre_false})

    # Bước 2: Gọi API cho bài còn lại
    if need_api:
        _run_api_filter(posts, need_api, results_map)
    else:
        print("  Tất cả bài đã được phân loại bằng keyword!")

    # Gán nhãn và đếm
    for i, post in enumerate(posts):
        post["is_relevant"] = results_map.get(i, False)
    relevant_count = sum(p["is_relevant"] for p in posts)

    output_path = _resolve_output_path(input_path)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n  ✓ Liên quan: {relevant_count}/{len(posts)} bài")
    print(f"  → {output_path}")
    return output_path


def _collect_input_files(args) -> list[str]:
    """Trả về danh sách đường dẫn file JSON cần xử lý, hoặc gọi sys.exit nếu lỗi."""
    if args.files:
        files = [os.path.abspath(f) for f in args.files]
        missing = [f for f in files if not os.path.exists(f)]
        if missing:
            for f in missing:
                print(f"[LỖI] Không tìm thấy file: {f}")
            sys.exit(1)
        return files

    if not os.path.isdir(DIRECTORY):
        print(f"[LỖI] Thư mục không tồn tại: {DIRECTORY}")
        sys.exit(1)
    return [
        os.path.join(DIRECTORY, f)
        for f in os.listdir(DIRECTORY)
        if f.startswith("cleaned_") and f.endswith(".json")
    ]


def main():
    global DIRECTORY

    parser = argparse.ArgumentParser(description="Lọc bài viết IT bằng Gemini API")
    parser.add_argument("files", nargs="*",
                        help="File cleaned_*.json cần xử lý (bỏ trống = scan --dir).")
    parser.add_argument("--dir", dest="directory", default=DIRECTORY,
                        help=f"Thư mục chứa cleaned_*.json (mặc định: {DIRECTORY}).")
    args = parser.parse_args()
    DIRECTORY = args.directory

    if API_KEY == "YOUR_API_KEY_HERE":
        print("[LỖI] Chưa cấu hình GEMINI_API_KEY (biến môi trường hoặc file .env).")
        sys.exit(1)

    json_files = _collect_input_files(args)
    if not json_files:
        print("Không tìm thấy file đầu vào.")
        return

    print(f"Tìm thấy {len(json_files)} file cần xử lý:")
    for f in json_files:
        print(f"  - {os.path.basename(f)}")

    for file_path in json_files:
        filter_json_file(file_path)

    print(f"\n{'=' * 55}")
    print("Hoàn thành! Kiểm tra các file filtered_data_*.json trong thư mục filtered_data")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
