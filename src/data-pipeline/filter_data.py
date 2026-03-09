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

SYSTEM_PROMPT = """You are a STRICT binary classifier for Vietnamese news article TITLES.

Your ONLY task: for each title, decide if the article is PRIMARILY about:
- AI (trí tuệ nhân tạo, machine learning, deep learning, mô hình ngôn ngữ)
- PROGRAMMING / SOFTWARE DEVELOPMENT / DEVTOOLS
- INFORMATION TECHNOLOGY JOBS & CAREERS (tuyển dụng, kỹ năng, lộ trình nghề nghiệp trong ngành CNTT)

If the main topic matches these, output YES.
Otherwise, output NO.

========================
WHAT COUNTS AS YES
========================

Label YES when the PRIMARY focus is:

1. AI & MACHINE LEARNING
   - AI models: LLMs, chatbots, generative AI, neural networks, computer vision, speech models
   - Ứng dụng AI: công cụ AI, trợ lý AI, tác nhân AI, AI trong doanh nghiệp/xã hội
   - Hạ tầng AI: huấn luyện mô hình, triển khai mô hình, tối ưu chi phí AI, GPU cloud cho AI
   - Chính sách/pháp luật về AI: quy định, đạo luật, chuẩn an toàn AI

2. SOFTWARE, APPS, PLATFORMS, DIGITAL SERVICES
   - Hệ điều hành, phần mềm máy tính/di động/web
   - Ứng dụng mobile/web, SaaS, cloud platforms, database, middleware
   - Dịch vụ số: mạng xã hội, nền tảng video, streaming, thương mại điện tử, thanh toán điện tử,
     ngân hàng số, ví điện tử, mobile banking, super app
   - Tính năng/phát hành/cập nhật của sản phẩm phần mềm hoặc dịch vụ số
   - Công cụ làm việc số: bộ văn phòng, phần mềm thiết kế, IDE, công cụ năng suất

3. PROGRAMMING, DEVELOPMENT, DEVTOOLS
   - Ngôn ngữ lập trình, framework, thư viện, SDK, API
   - Hướng dẫn, tips, best practices cho lập trình viên
   - Công cụ dev: GitHub, CI/CD, Docker, Kubernetes, hệ thống logging, monitoring
   - Open-source project, release mới, thay đổi license

4. CYBERSECURITY (PHẦN MỀM / MẠNG)
   - Tấn công mạng, malware, ransomware, lỗ hổng bảo mật, rò rỉ dữ liệu
   - Phần mềm/bộ giải pháp bảo mật, firewall, antivirus, VPN, xác thực, mã hóa
   - Sự cố bảo mật trên nền tảng số (mạng xã hội, dịch vụ cloud, ngân hàng số, ví điện tử)

5. IT JOBS & CAREERS (CÔNG VIỆC LIÊN QUAN CNTT)
   - Tuyển dụng, thông báo việc làm, mô tả vị trí, mức lương cho:
     lập trình viên, kỹ sư phần mềm, data engineer, data scientist, ML engineer,
     DevOps, QA/QC, tester, BA, PM phần mềm, kiến trúc sư giải pháp, kỹ sư bảo mật, admin hệ thống
   - Khóa học, chứng chỉ, kỹ năng dành cho nghề IT / lập trình / AI
   - Phân tích xu hướng nghề nghiệp, nhu cầu tuyển dụng, lộ trình nghề nghiệp trong ngành CNTT
   - Ví dụ YES:
     - "TopCV: Tuyển dụng Python Developer lương 30 triệu"
     - "Nhu cầu kỹ sư AI tăng mạnh tại Việt Nam"
     - "Khóa học lập trình web full-stack cho người mới bắt đầu"

6. COMPANY NEWS – ONLY IF TRỌNG TÂM LÀ SẢN PHẨM PHẦN MỀM/AI HOẶC NHÂN SỰ IT
   - Ra mắt / cập nhật / chiến lược liên quan đến sản phẩm phần mềm hoặc AI cụ thể
   - Chiến lược tuyển dụng/đào tạo đội ngũ kỹ sư phần mềm, AI, data của doanh nghiệp
   - Ví dụ YES:
     - "OpenAI ra mắt GPT-6 với khả năng lập trình tốt hơn"
     - "Ngân hàng X tuyển 100 kỹ sư IT cho nền tảng ngân hàng số"

========================
WHAT COUNTS AS NO
========================

Luôn label NO nếu tiêu đề tập trung vào:

1. HARDWARE, THIẾT BỊ, GADGET
   - Điện thoại, laptop, tablet, PC, TV, màn hình, camera, tai nghe, thiết bị gia dụng
   - So sánh cấu hình, đánh giá, giá bán, khuyến mãi của thiết bị
   - Ví dụ NO:
     - "iPhone 17e khác gì 16e, có đáng nâng cấp?"
     - "Laptop màn hình gập kiêm máy chơi game"
     - "Điện thoại robot sẽ lên kệ trong năm nay"

2. VIỄN THÔNG & HẠ TẦNG MẠNG
   - 5G, 6G, cáp quang, trạm phát sóng, hạ tầng viễn thông
   - Thử nghiệm 6G, mở rộng vùng phủ sóng, băng tần, gói cước
   - Ví dụ NO:
     - "TP HCM đề nghị ba nhà mạng cùng phát triển thí điểm 6G"
     - "Tốc độ mạng 5G Việt Nam tăng cao"

3. ĐIỆN TỬ TIÊU DÙNG, ĐỒ GIA DỤNG, XE CỘ
   - Tủ lạnh, máy giặt, máy hút ẩm, robot hút bụi, điều hòa, ô tô/xemáy (kể cả xe điện)
   - Ví dụ NO:
     - "Máy hút ẩm có khử khuẩn plasma"
     - "Galaxy S26 Ultra đọ pin với iPhone 17 Pro Max"

4. TÀI CHÍNH, KINH DOANH, CHỨNG KHOÁN (KHÔNG TRỌNG TÂM VÀO PHẦN MỀM/AI/IT JOBS)
   - Kết quả kinh doanh, IPO, cổ phiếu, M&A, gọi vốn
   - Tin chung về nền kinh tế, bất động sản, vàng, lãi suất
   - Ví dụ NO:
     - "Cổ phiếu công ty X tăng mạnh sau báo cáo tài chính"
     - "Giá vàng lập đỉnh mới"

5. CÁC LĨNH VỰC KHÁC
   - Thể thao, giải trí, thời trang, sức khỏe, y tế, giáo dục, môi trường, thiên văn, chính trị
   - Công việc không liên quan đến CNTT (bán hàng, marketing, chăm sóc khách hàng, tài xế, phục vụ…)
   - Kể cả khi có nhắc tới công nghệ nhưng không phải trọng tâm bài
   - Ví dụ NO:
     - "Xôi lạc TV và những 'cánh tay nối dài' của cá độ"
     - "Đội tuyển bóng đá sử dụng phân tích dữ liệu để nâng cao thành tích"

========================
STRICT BOUNDARY RULES
========================

1. Bài review/thông số/giá bán thiết bị PHẦN CỨNG luôn là NO, kể cả khi có AI bên trong.
2. Bài về doanh thu, cổ phiếu, thương vụ của công ty công nghệ là NO,
   trừ khi tiêu đề nói rõ về SẢN PHẨM phần mềm/AI hoặc TUYỂN DỤNG/KỸ NĂNG IT cụ thể.
3. Bài về luật, quy định, chiến lược quốc gia VỀ AI HAY CHUYỂN ĐỔI SỐ là YES.
4. Sự cố bảo mật/phát tán dữ liệu trên nền tảng số, hệ thống mạng là YES.
5. Khi có nhiều chủ đề trong 1 title, hãy chọn CHỦ ĐỀ CHÍNH. Nếu không rõ ràng, chọn NO.
6. Khi phân vân, LUÔN chọn NO.

========================
OUTPUT FORMAT
========================

Bạn sẽ nhận được một danh sách tiêu đề dạng:

1. Tiêu đề thứ nhất
2. Tiêu đề thứ hai
3. Tiêu đề thứ ba
...

Hãy trả về KẾT QUẢ DUY NHẤT theo đúng định dạng sau, không thêm giải thích:

1. YES
2. NO
3. YES
4. NO
...

Chỉ dùng YES hoặc NO. Không thêm bất kỳ chữ nào khác."""

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
WHITELIST_L = [kw.lower() for kw in WHITELIST]
BLACKLIST_L = [kw.lower() for kw in BLACKLIST]


def keyword_filter(title: str):
    """
    Kiểm tra nhanh bằng từ khoá trước khi gọi API.
    Returns:
        True   → chắc chắn liên quan, bỏ qua API
        False  → chắc chắn không liên quan, bỏ qua API
        None   → không chắc, cần gọi API
    """
    t = title.lower()
    for kw in BLACKLIST_L:
        if kw in t:
            return False
    for kw in WHITELIST_L:
        if kw in t:
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

def filter_json_file(input_path: str) -> str:
    """
    Đọc file cleaned JSON, gán nhãn is_relevant cho mỗi bài bằng batch API,
    ghi ra file mới với tiền tố 'filtered_data_' trong thư mục filtered_data.

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
        is_it = results_map.get(i, False)
        post["is_relevant"] = is_it
        if is_it:
            relevant_count += 1

    # Lưu file output vào thư mục filtered_data với tên dạng filtered_data_XXX.json
    os.makedirs(FILTERED_DATA_DIR, exist_ok=True)
    base_name = os.path.basename(input_path)

    # Nếu input là cleaned_data_XXX.json → output filtered_data_XXX.json
    if base_name.startswith("cleaned_data_"):
        suffix = base_name[len("cleaned_data_"):]  # phần XXX.json
    # Trường hợp cũ: cleaned_XXX.json → filtered_data_XXX.json
    elif base_name.startswith("cleaned_"):
        suffix = base_name[len("cleaned_"):]       # phần XXX.json
    else:
        suffix = base_name

    output_filename = "filtered_data_" + suffix
    output_path = os.path.join(FILTERED_DATA_DIR, output_filename)

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

    global DIRECTORY

    parser = argparse.ArgumentParser(description="Lọc bài viết IT bằng Gemini API")
    parser.add_argument(
        "files",
        nargs="*",
        help=(
            "Đường dẫn file cleaned_*.json cần xử lý. "
            "Nếu bỏ trống, script sẽ tự scan thư mục mặc định hoặc --dir."
        ),
    )
    parser.add_argument(
        "--dir",
        dest="directory",
        default=DIRECTORY,
        help=f"Thư mục chứa file cleaned_*.json (mặc định: {DIRECTORY}).",
    )

    args = parser.parse_args()

    # Cập nhật thư mục runtime từ argument
    DIRECTORY = args.directory

    if API_KEY == "YOUR_API_KEY_HERE":
        print("=" * 55)
        print("  LỖI: Chưa cấu hình API Key Gemini.")
        print("  - Đặt biến môi trường GEMINI_API_KEY trong hệ thống")
        print("  - Hoặc khai báo GEMINI_API_KEY trong file .env")
        print("=" * 55)
        sys.exit(1)

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
        if not os.path.isdir(DIRECTORY):
            print(f"[LỖI] Thư mục không tồn tại: {DIRECTORY}")
            sys.exit(1)

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
    print("Hoàn thành! Kiểm tra các file filtered_data_*.json trong thư mục filtered_data")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
    # [Async upgrade]: import asyncio; asyncio.run(main())
