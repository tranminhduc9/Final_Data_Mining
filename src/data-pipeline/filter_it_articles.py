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

# Fix encoding cho Windows terminal
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ==========================================
# CẤU HÌNH - Chỉnh sửa tại đây
# ==========================================

API_KEY     = "AIzaSyCq1NC2f6putIUF-pX2Bvq0H_UcJpnX1xU"    #Dán API Key                 
DIRECTORY   = r"C:\Users\Admin\MyProject\ScrapeData"    # Thư mục chứa file cleaned_*.json
MODEL       = "gemini-2.0-flash"                  
BATCH_SIZE  = 10                                        # Số title gửi mỗi lần gọi API
DELAY       = 5.0                                       # Giây chờ giữa các batch (tránh rate limit)

# Khi nâng cấp async, thêm:
# MAX_CONCURRENT = 5                                    # Số batch chạy song song tối đa

# ==========================================
# KIỂM TRA CẤU HÌNH
# ==========================================

if API_KEY == "YOUR_API_KEY_HERE":
    print("=" * 55)
    print("  LỖI: Chưa điền API Key!")
    print("=" * 55)
    sys.exit(1)

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

SYSTEM_PROMPT = """You are a strict classifier for Vietnamese software and AI news articles.
Your sole task: determine whether each article is DIRECTLY about SOFTWARE, AI, or PROGRAMMING.

### CLASSIFY YES only if the article's PRIMARY subject is:
- AI & machine learning: LLMs, chatbots, generative AI, neural networks, AI models (e.g., ChatGPT, Gemini, Claude)
- AI applications: AI tools, AI regulation/law, AI ethics, AI use cases in business/society
- Software & platforms: operating systems, mobile/web apps, SaaS, cloud platforms (AWS, GCP, Azure), databases
- Programming & development: programming languages, frameworks, developer tools, open-source projects, APIs
- Cybersecurity (software-focused): malware, vulnerabilities, hacking, data breaches, security software
- Digital services: e-commerce platforms, social media platforms, streaming services (the service/software itself, not the company's business news)
- Software companies & their PRODUCTS: OpenAI, Google (software products), Meta (software), Microsoft (software)

### CLASSIFY NO if the article is about:
- Hardware & devices: smartphones, laptops, tablets, chips, DRAM, CPUs, GPUs, batteries, screens
  → Example NO: "iPhone 17e hỗ trợ MagSafe", "Xiaomi Pad 8 Pro", "Giá DRAM biến động theo giờ"
- Telecom & networks: 5G, 6G, fiber, network infrastructure, telecom companies (Viettel, VNPT, MobiFone)
  → Example NO: "TP HCM đề nghị ba nhà mạng cùng phát triển thí điểm 6G"
- Consumer electronics: TVs, cameras, smart home appliances, dehumidifiers, air purifiers
  → Example NO: "Dreame DD20 - máy hút ẩm có khử khuẩn plasma"
- Astronomy, medicine, politics, business, sports, culture, environment

### STRICT BOUNDARY RULES:
1. A device/gadget review is NEVER YES, even if the device runs AI software
2. A company's fundraising/IPO/stock news is NO, unless the article is specifically about their software product
3. AI regulation laws ARE YES (e.g., "Luật Trí tuệ nhân tạo") — policy directly about AI/software counts
4. Cybersecurity incidents involving software/networks ARE YES; physical hardware attacks are NO
5. When in doubt, choose NO — only label YES if software/AI is unmistakably the core subject

### OUTPUT FORMAT — return ONLY this, nothing else:
1. YES
2. NO
3. YES
..."""

# ==========================================
# KEYWORD PRE-FILTER (không tốn API quota)
# ==========================================

# Bài chứa từ khoá này → chắc chắn LIÊN QUAN → True ngay
WHITELIST = [
    # AI & mô hình ngôn ngữ
    "AI", "A.I", "chatbot", "GPT", "Claude", "Gemini", "LLM",
    "trí tuệ nhân tạo", "machine learning", "deep learning",
    "neural network", "GenAI", "generative AI", "AI tạo sinh",
    "OpenAI", "Anthropic", "Mistral", "Llama", "Grok", "Copilot",
    "mô hình AI", "học máy", "ảo giác AI", "tác nhân AI",
    # Phần mềm & nền tảng
    "phần mềm", "ứng dụng", "app", "lập trình", "mã nguồn",
    "open-source", "API", "hệ điều hành", "framework", "database",
    "cloud", "SaaS", "PaaS", "IaaS", "microservice", "DevOps",
    "GitHub", "Docker", "Kubernetes", "Linux", "Windows", "Android", "iOS",
    "Python", "JavaScript", "Java", "C++", "Go", "Rust", "Swift",
    "web app", "mobile app", "backend", "frontend", "full-stack",
    # Dữ liệu & điện toán đám mây
    "dữ liệu", "big data", "trung tâm dữ liệu", "data center",
    "AWS", "Azure", "GCP", "Google Cloud", "Oracle",
    # Bảo mật
    "bảo mật", "an ninh mạng", "malware", "hack", "hacker",
    "tấn công mạng", "DDoS", "rò rỉ dữ liệu", "lổ hổng bảo mật",
    "mã độc", "ransomware", "phần mềm độc hại", "lừa đảo trực tuyến",
    "VPN", "mã hóa", "xác thực", "firewall",
    # Công ty phần mềm & dịch vụ digital
    "Microsoft", "Google", "Meta", "Apple", "ChatGPT", "Samsung",
    "Netflix", "Spotify", "TikTok", "YouTube", "Facebook", "Instagram",
    "Zalo", "VNG", "FPT Software",
    # Luật & chính sách AI/số
    "Luật Trí tuệ nhân tạo", "luật AI", "quản lý AI", "chuyển đổi số",
    "kinh tế số", "thanh toán điện tử", "thương mại điện tử",
    # Robot & tự động hóa phần mềm
    "robot phần mềm", "tự động hóa", "RPA",
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
    "bơi lội", "điện kinh", "cầu lông", "quần vợt", "bắc cầu",
    # Văn hóa & giải trí
    "ca sĩ", "nghệ sĩ", "diễn viên", "phim", "album", "concert",
    "gameshow", "hoa hậu", "thời trang", "mỹ phẩm",
    # Y tế & sức khỏe
    "bệnh viện", "thuốc", "vắc xin", "dịch bệnh", "ung thư",
    "vi rút", "bác sĩ", "sức khỏe", "diện sinh lý",
    # Nông nghiệp & thực phẩm
    "nông nghiệp", "lúa gạo", "đại trà", "thực phẩm", "nhà hàng",
    "thủy sản", "chăn nuôi",
    # Tài chính thuần túy (không liên quan tech)
    "bất động sản", "cho vay", "lãi suất ngân hàng", "trái phiếu",
    "vàng", "bầu cử",
]


def keyword_filter(title: str):
    """
    Kiểm tra nhanh bằng từ khoá trước khi gọi API.
    Returns:
        True   → chắc chắn liên quan, bỏ qua API
        False  → chắc chắn không liên quan, bỏ qua API
        None   → không chắc, cần gọi API
    """
    t = title.lower()
    for kw in BLACKLIST:
        if kw.lower() in t:
            return False
    for kw in WHITELIST:
        if kw.lower() in t:
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
    MAX_RETRIES = 5
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
            raw = response.text.strip()

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
                print(f"    [WARN] Parse lệch ({len(results)} vs {len(titles)}) — giữ tất cả")
                return [True] * len(titles)

            return results

        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower():
                wait = BASE_DELAY * (2 ** attempt)  # 10s, 20s, 40s, 80s, 160s
                print(f"    [RATE LIMIT] Lần {attempt + 1}/{MAX_RETRIES} — chờ {wait}s rồi thử lại...")
                time.sleep(wait)
            else:
                print(f"    [WARN] Lỗi API: {e} — giữ tất cả bài trong batch này")
                return [True] * len(titles)

    print(f"    [ERROR] Đã thử {MAX_RETRIES} lần vẫn lỗi — giữ tất cả bài trong batch này")
    return [True] * len(titles)


def make_batches(lst: list, size: int) -> list[list]:
    """Chia list thành các batch có kích thước cố định."""
    return [lst[i:i + size] for i in range(0, len(lst), size)]


# ==========================================
# HÀM XỬ LÝ FILE JSON
# ==========================================

def filter_json_file(input_path: str) -> str:
    """
    Đọc file cleaned JSON, gán nhãn is_relevant cho mỗi bài bằng batch API,
    ghi ra file mới với tiền tố 'labeled_'.

    [Thiết kế để nâng cấp async]
    Khi nâng cấp: đổi thành async def filter_json_file()
    Dùng asyncio.gather() với Semaphore để chạy các batch đồng thời.
    """
    print(f"\n{'=' * 55}")
    print(f"Đang xử lý: {os.path.basename(input_path)}")
    print(f"{'=' * 55}")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    posts  = data.get("post_detail", [])
    total  = len(posts)
    print(f"Tổng số bài: {total}")

    # Bước 1: Keyword pre-filter (không tốn quota)
    pre_true, pre_false, need_api = [], [], []
    for i, post in enumerate(posts):
        result = keyword_filter(post.get("title", ""))
        if result is True:
            pre_true.append(i)
        elif result is False:
            pre_false.append(i)
        else:
            need_api.append(i)

    print(f"  Keyword filter: {len(pre_true)} liên quan ✓ | "
          f"{len(pre_false)} không liên quan ✗ | "
          f"{len(need_api)} cần hỏi API ?")

    # Khởi tạo kết quả từng bài, gán ngay cho những bài đã biết
    results_map = {}
    for i in pre_true:
        results_map[i] = True
    for i in pre_false:
        results_map[i] = False

    # Bước 2: Gọi API chỉ cho những bài chưa chắc
    if need_api:
        ambiguous_titles = [posts[i].get("title", "") for i in need_api]
        total_batches = -(-len(ambiguous_titles) // BATCH_SIZE)
        print(f"  Gọi API cho {len(ambiguous_titles)} bài → {total_batches} batch...")

        batches     = make_batches(ambiguous_titles, BATCH_SIZE)
        api_results = []

        for batch_idx, batch in enumerate(batches):
            start = batch_idx * BATCH_SIZE
            end   = start + len(batch)
            print(f"\n  Batch {batch_idx + 1}/{total_batches} (bài cần API: {start + 1}–{end})...")

            r = classify_batch(batch)
            api_results.extend(r)

            for j, (title, is_it) in enumerate(zip(batch, r)):
                mark  = "✓" if is_it else "✗"
                label = "true " if is_it else "false"
                print(f"    [{need_api[start + j] + 1}] {mark} is_relevant: {label} | {title[:50]}")

            if batch_idx < len(batches) - 1:
                time.sleep(DELAY)

        for i, idx in enumerate(need_api):
            results_map[idx] = api_results[i]
    else:
        print("  Tất cả bài đã được phân loại bằng keyword, không cần gọi API!")

    # Gán nhãn is_relevant vào từng bài
    relevant_count = 0
    for i, post in enumerate(posts):
        is_it = results_map.get(i, True)
        post["is_relevant"] = is_it
        if is_it:
            relevant_count += 1

    # Lưu file output
    dir_name   = os.path.dirname(input_path)
    base_name  = os.path.basename(input_path)
    clean_name = base_name.replace("cleaned_", "", 1)
    output_path = os.path.join(dir_name, "labeled_" + clean_name)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n  ✓ Liên quan IT:     {relevant_count}/{total} bài")
    print(f"  ✗ Không liên quan: {total - relevant_count}/{total} bài")
    print(f"  → Kết quả: {output_path}")
    return output_path


# ==========================================
# HÀM CHÍNH
# ==========================================

def main():
    # [Async upgrade]: đổi thành async def main(), chạy bằng asyncio.run(main())

    parser = argparse.ArgumentParser(description="Lọc bài viết IT bằng Gemini API")
    parser.add_argument(
        "files", nargs="*",
        help="Đường dẫn file cleaned_*.json cần xử lý. "
             "Nếu bỏ trống, tự scan thư mục DIRECTORY."
    )
    args = parser.parse_args()

    if args.files:
        # Chế độ chỉ định file cụ thể
        json_files = [os.path.abspath(f) for f in args.files]
        missing = [f for f in json_files if not os.path.exists(f)]
        if missing:
            for f in missing:
                print(f"[LỖI] Không tìm thấy file: {f}")
            sys.exit(1)
    else:
        # Fallback: scan DIRECTORY
        json_files = [
            os.path.join(DIRECTORY, f)
            for f in os.listdir(DIRECTORY)
            if f.startswith("cleaned_") and f.endswith(".json")
        ]

    if not json_files:
        print(f"Không tìm thấy file đầu vào.")
        return

    print(f"Tìm thấy {len(json_files)} file cần xử lý:")
    for f in json_files:
        print(f"  - {os.path.basename(f)}")

    for file_path in json_files:
        filter_json_file(file_path)

    print(f"\n{'=' * 55}")
    print("Hoàn thành! Kiểm tra các file labeled_*.json")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
    # [Async upgrade]: import asyncio; asyncio.run(main())
