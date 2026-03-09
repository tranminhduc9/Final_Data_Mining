"""
==========================================================
  SCRIPT TRÍCH XUẤT THỰC THỂ (NER) - HYBRID
  Chiến lược: Rule-based + Dictionary → LLM → Merge
==========================================================

PIPELINE:
  1. Rule-based extract  → bắt entity đã biết (từ điển + regex, offline)
  2. LLM extract         → mọi bài đều gọi LLM để bổ sung person, event, salary...
  3. Merge + Normalize   → gộp kết quả từ điển + LLM, chuẩn hóa tên entity
  4. Save JSON
"""

import argparse
import json
import os
import re
import sys
import time

from dotenv import load_dotenv

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

# ==========================================
# CẤU HÌNH - Chỉnh sửa tại đây
# ==========================================

API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")  # Lấy API Key từ GEMINI_API_KEY trong .env

# Thư mục gốc project (dựa trên vị trí file hiện tại)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Thư mục chứa file filtered_data_*.json (output sau bước lọc IT)
FILTERED_DATA_DIR = os.path.join(BASE_DIR, "filtered_data")

# Thư mục chứa file extracted_data_*.json (output sau bước NER)
EXTRACTED_DATA_DIR = os.path.join(BASE_DIR, "extracted_data")

# Thư mục mặc định để scan input (có thể override bằng --dir)
DIRECTORY = FILTERED_DATA_DIR

MODEL      = "gemma-3-27b-it"   # Model mặc định
BATCH_SIZE = 10                   # Số bài gửi mỗi lần gọi API
DELAY      = 10.0                 # Giây chờ giữa các batch (tránh rate limit)

try:
    from google import genai
except ImportError:
    print("=" * 55)
    print("  LỖI: Chưa cài thư viện google-genai!")
    print("=" * 55)
    sys.exit(1)

client = genai.Client(api_key=API_KEY)

# ==========================================
# SCHEMA ENTITY (12 trường)
# ==========================================

EMPTY_ENTITIES = {
    "organizations":         [],
    "products":              [],
    "technologies":          [],
    "programming_languages": [],
    "frameworks_tools":      [],
    "job_titles":            [],
    "salary":                [],
    "events":                [],
    "locations":             [],
    "persons":               [],
    "laws":                  [],
    "vulnerabilities":       [],
}


def empty_entities() -> dict:
    """Tạo bản copy entity rỗng (tránh dùng chung reference)."""
    return {k: [] for k in EMPTY_ENTITIES}

# ==========================================
# RULE-BASED: DICTIONARY + REGEX
# ==========================================

# Từ điển entity đã biết — {từ khoá (lowercase): trường entity}
ENTITY_DICT: dict[str, tuple[str, str]] = {
    # (field, display_name) — display_name là cách hiển thị chuẩn

    # Organizations
    "apple":       ("organizations", "Apple"),
    "samsung":     ("organizations", "Samsung"),
    "google":      ("organizations", "Google"),
    "meta":        ("organizations", "Meta"),
    "microsoft":   ("organizations", "Microsoft"),
    "openai":      ("organizations", "OpenAI"),
    "anthropic":   ("organizations", "Anthropic"),
    "mistral":     ("organizations", "Mistral"),
    "nvidia":      ("organizations", "NVIDIA"),
    "intel":       ("organizations", "Intel"),
    "amd":         ("organizations", "AMD"),
    "qualcomm":    ("organizations", "Qualcomm"),
    "viettel":     ("organizations", "Viettel"),
    "fpt":         ("organizations", "FPT"),
    "vnpt":        ("organizations", "VNPT"),
    "vng":         ("organizations", "VNG"),
    "xiaomi":      ("organizations", "Xiaomi"),
    "motorola":    ("organizations", "Motorola"),
    "lenovo":      ("organizations", "Lenovo"),
    "honor":       ("organizations", "Honor"),
    "panasonic":   ("organizations", "Panasonic"),
    "sony":        ("organizations", "Sony"),
    "lg":          ("organizations", "LG"),
    "asus":        ("organizations", "ASUS"),
    "huawei":      ("organizations", "Huawei"),
    "oppo":        ("organizations", "OPPO"),
    "realme":      ("organizations", "Realme"),
    "amazon":      ("organizations", "Amazon"),
    "netflix":     ("organizations", "Netflix"),
    "spotify":     ("organizations", "Spotify"),
    "tiktok":      ("organizations", "TikTok"),
    # Báo / tin tức IT Việt Nam
    "dân trí":     ("organizations", "Dân trí"),
    "dantri":      ("organizations", "Dân trí"),
    "vnexpress":   ("organizations", "VNExpress"),
    "vn express":  ("organizations", "VNExpress"),
    "zing":        ("organizations", "Zing"),
    "thanh niên":  ("organizations", "Thanh Niên"),
    "tuổi trẻ":    ("organizations", "Tuổi Trẻ"),
    "cafef":       ("organizations", "Cafef"),
    "ictnews":     ("organizations", "ICT News"),
    "vietnamnet":  ("organizations", "VietnamNet"),
    "vnn":         ("organizations", "VietnamNet"),
    "vneconomy":   ("organizations", "VnEconomy"),
    "vccorp":      ("organizations", "VCCorp"),
    "coccoc":      ("organizations", "Coc Coc"),
    "tinhte":      ("organizations", "Tinhte"),
    "genk":        ("organizations", "GenK"),
    # Tuyển dụng / việc làm IT
    "topcv":       ("organizations", "TopCV"),
    "top cv":      ("organizations", "TopCV"),
    "vietnamworks": ("organizations", "VietnamWorks"),
    "careerbuilder": ("organizations", "CareerBuilder"),
    "linkedin":    ("organizations", "LinkedIn"),
    "jobstreet":   ("organizations", "JobStreet"),
    "indeed":      ("organizations", "Indeed"),
    "glints":      ("organizations", "Glints"),
    "navigos":     ("organizations", "Navigos"),
    "careerlink":  ("organizations", "CareerLink"),
    "vieclam24h":  ("organizations", "Vieclam24h"),
    "itviec":      ("organizations", "ITviec"),
    # Công ty IT Việt Nam / outsourcing
    "cmc":         ("organizations", "CMC"),
    "tma":         ("organizations", "TMA"),
    "kms":         ("organizations", "KMS"),
    "nashtech":    ("organizations", "NashTech"),
    "rikkeisoft":  ("organizations", "Rikkeisoft"),
    "mgm":         ("organizations", "MGM"),
    "brave":       ("organizations", "Brave"),
    "mobifone":    ("organizations", "MobiFone"),
    "vinaphone":   ("organizations", "Vinaphone"),
    "vinadata":    ("organizations", "VinaData"),
    "bkav":        ("organizations", "Bkav"),
    "sendo":       ("organizations", "Sendo"),
    "tiki":        ("organizations", "Tiki"),
    "shopee":      ("organizations", "Shopee"),
    "lazada":      ("organizations", "Lazada"),
    "momo":        ("organizations", "MoMo"),
    "vnpay":       ("organizations", "VNPay"),
    "zalo pay":    ("organizations", "ZaloPay"),
    "grab":        ("organizations", "Grab"),

    # Products
    "chatgpt":     ("products", "ChatGPT"),
    "claude":      ("products", "Claude"),
    "gemini":      ("products", "Gemini"),
    "copilot":     ("products", "Copilot"),
    "grok":        ("products", "Grok"),
    "llama":       ("products", "Llama"),
    "zalo":        ("products", "Zalo"),
    "viber":       ("products", "Viber"),
    "telegram":    ("products", "Telegram"),
    "slack":       ("products", "Slack"),
    "teams":       ("products", "Microsoft Teams"),
    "zoom":        ("products", "Zoom"),
    "notion":      ("products", "Notion"),
    "figma":       ("products", "Figma"),
    "jira":        ("products", "Jira"),
    "confluence":  ("products", "Confluence"),
    "trello":      ("products", "Trello"),
    "vscode":      ("products", "VS Code"),
    "android":     ("products", "Android"),
    "ios":         ("products", "iOS"),
    "windows":     ("products", "Windows"),
    "linux":       ("products", "Linux"),

    # Technologies
    "ai":          ("technologies", "AI"),
    "5g":          ("technologies", "5G"),
    "6g":          ("technologies", "6G"),
    "blockchain":  ("technologies", "blockchain"),
    "cloud":       ("technologies", "cloud"),
    "iot":         ("technologies", "IoT"),
    "ar":          ("technologies", "AR"),
    "vr":          ("technologies", "VR"),
    "ddos":        ("technologies", "DDoS"),
    "genai":       ("technologies", "GenAI"),
    "llm":         ("technologies", "LLM"),
    "rag":         ("technologies", "RAG"),
    "machine learning": ("technologies", "Machine Learning"),
    "deep learning": ("technologies", "Deep Learning"),
    "big data":    ("technologies", "Big Data"),
    "cybersecurity": ("technologies", "Cybersecurity"),
    "an ninh mạng": ("technologies", "An ninh mạng"),
    "chuyển đổi số": ("technologies", "Chuyển đổi số"),
    "kinh tế số":  ("technologies", "Kinh tế số"),
    "microservice": ("technologies", "Microservice"),
    "api":         ("technologies", "API"),
    "devops":      ("technologies", "DevOps"),
    "agile":       ("technologies", "Agile"),
    "scrum":       ("technologies", "Scrum"),

    # Programming languages
    "python":      ("programming_languages", "Python"),
    "javascript":  ("programming_languages", "JavaScript"),
    "typescript":  ("programming_languages", "TypeScript"),
    "java":        ("programming_languages", "Java"),
    "kotlin":      ("programming_languages", "Kotlin"),
    "swift":       ("programming_languages", "Swift"),
    "go":          ("programming_languages", "Go"),
    "rust":        ("programming_languages", "Rust"),
    "c++":         ("programming_languages", "C++"),
    "c#":          ("programming_languages", "C#"),
    "php":         ("programming_languages", "PHP"),
    "ruby":        ("programming_languages", "Ruby"),
    "scala":       ("programming_languages", "Scala"),
    "r":           ("programming_languages", "R"),
    "dart":        ("programming_languages", "Dart"),
    "sql":         ("programming_languages", "SQL"),

    # Frameworks & Tools
    "react":       ("frameworks_tools", "React"),
    "vue":         ("frameworks_tools", "Vue.js"),
    "angular":     ("frameworks_tools", "Angular"),
    "django":      ("frameworks_tools", "Django"),
    "fastapi":     ("frameworks_tools", "FastAPI"),
    "flask":       ("frameworks_tools", "Flask"),
    "spring":      ("frameworks_tools", "Spring"),
    "laravel":     ("frameworks_tools", "Laravel"),
    "docker":      ("frameworks_tools", "Docker"),
    "kubernetes":  ("frameworks_tools", "Kubernetes"),
    "k8s":         ("frameworks_tools", "Kubernetes"),
    "github":      ("frameworks_tools", "GitHub"),
    "gitlab":      ("frameworks_tools", "GitLab"),
    "jenkins":     ("frameworks_tools", "Jenkins"),
    "tensorflow":  ("frameworks_tools", "TensorFlow"),
    "pytorch":     ("frameworks_tools", "PyTorch"),
    "kafka":       ("frameworks_tools", "Kafka"),
    "redis":       ("frameworks_tools", "Redis"),
    "mongodb":     ("frameworks_tools", "MongoDB"),
    "postgresql":  ("frameworks_tools", "PostgreSQL"),
    "mysql":       ("frameworks_tools", "MySQL"),
    "elasticsearch": ("frameworks_tools", "Elasticsearch"),
    "next.js":     ("frameworks_tools", "Next.js"),
    "nuxt":        ("frameworks_tools", "Nuxt"),
    "nodejs":      ("frameworks_tools", "Node.js"),
    "nestjs":      ("frameworks_tools", "NestJS"),
    "graphql":     ("frameworks_tools", "GraphQL"),
    "terraform":   ("frameworks_tools", "Terraform"),
    "aws":         ("frameworks_tools", "AWS"),
    "azure":       ("frameworks_tools", "Azure"),
    "gcp":         ("frameworks_tools", "Google Cloud"),

    # Job titles (việc làm IT)
    "lập trình viên": ("job_titles", "Lập trình viên"),
    "developer":   ("job_titles", "Developer"),
    "kỹ sư phần mềm": ("job_titles", "Kỹ sư phần mềm"),
    "software engineer": ("job_titles", "Software Engineer"),
    "data scientist": ("job_titles", "Data Scientist"),
    "data engineer": ("job_titles", "Data Engineer"),
    "ml engineer": ("job_titles", "ML Engineer"),
    "devops engineer": ("job_titles", "DevOps Engineer"),
    "qa":          ("job_titles", "QA"),
    "tester":      ("job_titles", "Tester"),
    "business analyst": ("job_titles", "Business Analyst"),
    "product manager": ("job_titles", "Product Manager"),
    "scrum master": ("job_titles", "Scrum Master"),
    "cto":         ("job_titles", "CTO"),
    "fullstack":   ("job_titles", "Full-stack"),
    "full-stack":  ("job_titles", "Full-stack"),
    "backend":     ("job_titles", "Backend"),
    "frontend":    ("job_titles", "Frontend"),
    "kiến trúc sư phần mềm": ("job_titles", "Kiến trúc sư phần mềm"),
    "kỹ sư bảo mật": ("job_titles", "Kỹ sư bảo mật"),
    "it support":  ("job_titles", "IT Support"),

    # Locations
    "việt nam":    ("locations", "Việt Nam"),
    "hà nội":      ("locations", "Hà Nội"),
    "tp hcm":      ("locations", "TP.HCM"),
    "hồ chí minh": ("locations", "TP.HCM"),
    "mỹ":          ("locations", "Mỹ"),
    "trung quốc":  ("locations", "Trung Quốc"),
    "nhật bản":    ("locations", "Nhật Bản"),
    "hàn quốc":    ("locations", "Hàn Quốc"),
    "barcelona":   ("locations", "Barcelona"),
    "singapore":   ("locations", "Singapore"),
    "iran":        ("locations", "Iran"),
    "đà nẵng":     ("locations", "Đà Nẵng"),
    "cần thơ":     ("locations", "Cần Thơ"),
    "bình dương":  ("locations", "Bình Dương"),
    "đồng nai":    ("locations", "Đồng Nai"),
    "hải phòng":   ("locations", "Hải Phòng"),
    "silicon valley": ("locations", "Silicon Valley"),
    "california":  ("locations", "California"),
    "seattle":     ("locations", "Seattle"),
    "ấn độ":       ("locations", "Ấn Độ"),
    "india":       ("locations", "Ấn Độ"),
    "châu âu":     ("locations", "Châu Âu"),
    "eu":          ("locations", "Châu Âu"),
    "anh":         ("locations", "Anh"),
    "uk":          ("locations", "Anh"),
    "đài loan":    ("locations", "Đài Loan"),
    "taiwan":      ("locations", "Đài Loan"),

    # Laws
    "luật trí tuệ nhân tạo":   ("laws", "Luật Trí tuệ nhân tạo 2025"),
    "luật ai":                  ("laws", "Luật AI 2025"),
    "gdpr":                     ("laws", "GDPR"),
    "luật an ninh mạng":        ("laws", "Luật An ninh mạng"),
    "nghị định 13":             ("laws", "Nghị định 13/2023"),
    "luật số hóa":              ("laws", "Luật Chuyển đổi số"),
}

# ==========================================
# ENTITY NORMALIZATION
# ==========================================

# Bản đồ chuẩn hóa alias → tên chuẩn (lowercase key)
NORMALIZATION_MAP: dict[str, str] = {
    # Locations
    "viet nam":              "Việt Nam",
    "vietnam":               "Việt Nam",
    "vn":                    "Việt Nam",
    "ho chi minh":           "TP.HCM",
    "ho chi minh city":      "TP.HCM",
    "tp hồ chí minh":       "TP.HCM",
    "hồ chí minh":          "TP.HCM",
    "tp. hồ chí minh":      "TP.HCM",
    "ha noi":                "Hà Nội",
    "hanoi":                 "Hà Nội",
    "usa":                   "Mỹ",
    "united states":         "Mỹ",
    "us":                    "Mỹ",
    "china":                 "Trung Quốc",
    "japan":                 "Nhật Bản",
    "south korea":           "Hàn Quốc",
    "korea":                 "Hàn Quốc",
    # Organizations
    "apple inc":             "Apple",
    "apple inc.":            "Apple",
    "google llc":            "Google",
    "alphabet":              "Google",
    "meta platforms":        "Meta",
    "facebook":              "Meta",
    "microsoft corporation": "Microsoft",
    "openai lp":             "OpenAI",
    "tập đoàn fpt":          "FPT",
    "fpt software":          "FPT",
    "viettel group":         "Viettel",
    "tập đoàn viettel":      "Viettel",
    # Technologies
    "artificial intelligence": "AI",
    "artificial intelligence (ai)": "AI",
    "trí tuệ nhân tạo":     "AI",
    "machine learning":      "Machine Learning",
    "internet of things":    "IoT",
    "augmented reality":     "AR",
    "virtual reality":       "VR",
    # Programming languages
    "js":                    "JavaScript",
    "ts":                    "TypeScript",
    "golang":                "Go",
    "cpp":                   "C++",
    "csharp":                "C#",
    # Frameworks
    "k8s":                   "Kubernetes",
    "vue.js":                "Vue.js",
    "next.js":               "Next.js",
    "nuxt.js":               "Nuxt.js",
    "node.js":               "Node.js",
    "nodejs":                "Node.js",
    "reactjs":               "React",
    "react.js":              "React",
    "angularjs":             "Angular",
    "pytorch":               "PyTorch",
    # Báo / nguồn tin
    "dantri":                "Dân trí",
    "báo dân trí":           "Dân trí",
    "vn express":            "VNExpress",
    "vnexpress":             "VNExpress",
    "báo thanh niên":        "Thanh Niên",
    "báo tuổi trẻ":          "Tuổi Trẻ",
    "ict news":              "ICT News",
    "vietnam net":           "VietnamNet",
    "genk":                  "GenK",
    "tinhte":                "Tinhte",
    # Tuyển dụng
    "top cv":                "TopCV",
    "topcv":                 "TopCV",
    "vietnam works":         "VietnamWorks",
    "career builder":        "CareerBuilder",
    "job street":            "JobStreet",
    "it viec":               "ITviec",
    "viec lam 24h":          "Vieclam24h",
    "career link":           "CareerLink",
    # Công ty IT VN
    "fpt software":          "FPT",
    "tập đoàn fpt":          "FPT",
    "cmc corporation":       "CMC",
    "tma solutions":          "TMA",
    "kms technology":        "KMS",
    "nash tech":             "NashTech",
    "rikkei":                "Rikkeisoft",
    "mobi fone":             "MobiFone",
    "vina phone":            "Vinaphone",
    "coc coc":               "Coc Coc",
    "coccoc":                "Coc Coc",
    # Sản phẩm / công nghệ
    "vs code":               "VS Code",
    "visual studio code":    "VS Code",
    "node js":               "Node.js",
    "google cloud":          "Google Cloud",
    "machine learning":      "Machine Learning",
    "deep learning":         "Deep Learning",
    "trí tuệ nhân tạo":      "AI",
    "học máy":               "Machine Learning",
    # Địa điểm
    "đà nẵng":               "Đà Nẵng",
    "da nang":               "Đà Nẵng",
    "can tho":               "Cần Thơ",
    "binh duong":            "Bình Dương",
    "dong nai":              "Đồng Nai",
    "hai phong":             "Hải Phòng",
    "silicon valley":        "Silicon Valley",
    "an do":                 "Ấn Độ",
    "india":                 "Ấn Độ",
    "chau au":               "Châu Âu",
    "europe":                "Châu Âu",
    "united kingdom":        "Anh",
    "dai loan":              "Đài Loan",
    "taiwan":                "Đài Loan",
}


def normalize_entity(text: str) -> str:
    """
    Chuẩn hóa tên entity:
    - Tra bảng NORMALIZATION_MAP (alias → tên chuẩn)
    - Xóa khoảng trắng thừa ở đầu/cuối
    """
    stripped = text.strip()
    mapped = NORMALIZATION_MAP.get(stripped.lower())
    return mapped if mapped else stripped

# Regex patterns cho entity có cấu trúc
REGEX_PATTERNS: dict[str, list[str]] = {
    "vulnerabilities": [
        r"CVE-\d{4}-\d{4,7}",          # CVE-2025-12345
        r"Log4Shell",
        r"EternalBlue",
        r"Heartbleed",
    ],
    "salary": [
        r"\d+[-–]\d+\s*triệu(?:\s*đồng)?",       # 20-30 triệu
        r"\$\s*\d+(?:[.,]\d+)?[-–]\$?\s*\d+",    # $2000-3000
        r"(?:lương\s+)?(?:từ\s+)?\d+\+?\s*triệu",  # 25 triệu / 25+ triệu
        # Chú ý: KHÔNG match 'thỏa thuận' trực tiếp ở đây,
        # tránh bắt nhầm các bài không phải tin tuyển dụng.
        r"competitive",
    ],
    "products": [
        r"iPhone\s+\d+[e\s]?\w*",       # iPhone 17e, iPhone 17 Pro Max
        r"Galaxy\s+[A-Z]\d+\+?\s*\w*",  # Galaxy S26, Galaxy Z Fold 7
        r"MacBook\s+\w+(?: \w+)?",       # MacBook Neo, MacBook Pro M5
        r"iPad\s+\w+(?: \w+)?",          # iPad Air M4
        r"Pixel\s+\d+\w*",               # Pixel 9 Pro
        r"GPT[-\s]?\d+(?:\.\d+)?",       # GPT-5, GPT-4.5
        r"Claude[-\s]\d+(?:\.\d+)?",     # Claude-3.5
    ],
    "events": [
        r"MWC\s+\d{4}",         # MWC 2026
        r"CES\s+\d{4}",         # CES 2026
        r"Google\s+I/O",        # Google I/O
        r"WWDC\s+\d{4}",        # WWDC 2026
        r"Black\s*Hat",
        r"DEF\s*CON",
    ],
}

# Compile regex một lần khi load (tối ưu hiệu năng)
REGEX_COMPILED: dict[str, list[re.Pattern]] = {
    field: [re.compile(p, re.IGNORECASE) for p in patterns]
    for field, patterns in REGEX_PATTERNS.items()
}

# Từ có độ dài <= SHORT_TERM_LEN cần match theo word boundary (tránh "go" trong "Google", "r" trong "React")
SHORT_TERM_LEN = 3


def _term_matches(term: str, text_lower: str) -> bool:
    """Match term trong text: từ ngắn (<=SHORT_TERM_LEN) dùng word boundary."""
    if len(term) <= SHORT_TERM_LEN:
        return bool(re.search(r"\b" + re.escape(term) + r"\b", text_lower))
    return term in text_lower


def rule_based_extract(text: str) -> dict[str, list[str]]:
    """
    Trích xuất entity từ text bằng dictionary lookup và regex.
    Trả về dict cùng schema với EMPTY_ENTITIES.
    Từ ngắn (go, r, ai, lg...) chỉ match theo word boundary để tránh false positive.
    """
    result: dict[str, list[str]] = {k: [] for k in EMPTY_ENTITIES}
    text_lower = text.lower()

    # 1. Dictionary lookup (word boundary cho từ ngắn)
    for term, (field, display) in ENTITY_DICT.items():
        if _term_matches(term, text_lower):
            if display not in result[field]:
                result[field].append(display)

    # 2. Regex patterns (dùng compiled)
    for field, compiled_list in REGEX_COMPILED.items():
        for pattern in compiled_list:
            matches = pattern.findall(text)
            for m in matches:
                m = m.strip() if isinstance(m, str) else str(m).strip()
                if m and m not in result[field]:
                    result[field].append(m)

    return result


def merge_entities(rule_result: dict, llm_result: dict) -> dict:
    """
    Gộp kết quả rule-based và LLM:
    1. Normalize tên entity qua NORMALIZATION_MAP
    2. Loai trùng lặp (case-insensitive)
    Rule-based ưu tiên display name chuẩn hóa, LLM bổ sung phần còn lại.
    """
    merged = {k: [] for k in EMPTY_ENTITIES}

    for field in EMPTY_ENTITIES:
        seen_lower = set()
        combined = rule_result.get(field, []) + llm_result.get(field, [])
        for item in combined:
            item = normalize_entity(item)  # ← Normalize trước khi dedup
            if item and item.lower() not in seen_lower:
                merged[field].append(item)
                seen_lower.add(item.lower())

    return merged


# ==========================================
# HẬU XỬ LÝ SALARY ("THỎA THUẬN")
# ==========================================

JOB_SALARY_KEYWORDS = [
    "tuyển", "tuyển dụng", "việc làm", "ứng viên",
    "nhân sự", "tuyển nhân viên", "tìm người",
    "lương", "mức lương", "thu nhập",
    "developer", "lập trình viên", "kỹ sư phần mềm",
    "software engineer", "data scientist", "data engineer",
    "devops", "qa", "tester", "it",
]


def _has_job_context(title: str, description: str, entities: dict) -> bool:
    """Kiểm tra xem bài viết có ngữ cảnh tuyển dụng / việc làm hay không."""
    # Nếu LLM hoặc rule-based đã bắt được job_titles thì coi như bài tuyển dụng
    if entities.get("job_titles"):
        return True

    text = f"{title} {description}".lower()
    return any(kw in text for kw in JOB_SALARY_KEYWORDS)


def postprocess_salary(entities: dict, title: str, description: str) -> None:
    """
    Làm sạch lại trường salary sau khi merge:
    - Loại bỏ các entry chỉ là 'thỏa thuận' nếu bài viết KHÔNG có ngữ cảnh tuyển dụng.
    Giữ nguyên các mức lương có số hoặc các cụm khác.
    """
    salaries = entities.get("salary") or []
    if not salaries:
        return

    has_job_ctx = _has_job_context(title, description, entities)

    cleaned = []
    for s in salaries:
        s_norm = s.strip()
        if s_norm.lower() in {"thỏa thuận", "thoả thuận"} and not has_job_ctx:
            # Bài không phải tuyển dụng → bỏ 'thỏa thuận' mơ hồ
            continue
        cleaned.append(s_norm)

    entities["salary"] = cleaned


# ==========================================
# LLM EXTRACTION
# ==========================================

SYSTEM_PROMPT = """Bạn là hệ thống trích xuất thực thể có tên (NER) cho nội dung tiếng Việt về CNTT và tuyển dụng IT.

## NHIỆT VỤ
Trích xuất đúng 12 loại entity từ mỗi bài (title + description). Trả về một mảng JSON, mỗi phần tử là một object tương ứng với từng bài, theo đúng thứ tự bài được đưa vào.

## NGUỒN BÀI VIẾT
- Tin tức IT (Dân Trí, VNExpress, Zing, ICT News...): công ty, sản phẩm, công nghệ, sự kiện, nhân vật, địa điểm, luật.
- Tin tuyển dụng IT (TopCV, VietnamWorks...): công ty tuyển dụng, vị trí công việc, mức lương, kỹ năng, địa điểm làm việc.

## 12 TRƯỜNG BẮT BUỘC (luôn trả về đủ 12 key, dùng [] nếu không tìm thấy)

1. **organizations** — Tên công ty, tổ chức, cơ quan (VD: FPT, Viettel, OpenAI, TopCV, Dân trí).
2. **products** — Tên sản phẩm phần mềm/hardware, ứng dụng (VD: ChatGPT, Zalo, MacBook Neo, Android, Windows).
3. **technologies** — Công nghệ nói chung (VD: AI, 5G, cloud, blockchain, machine learning, chuyển đổi số).
4. **programming_languages** — Ngôn ngữ lập trình (VD: Python, Java, JavaScript, C++, Go).
5. **frameworks_tools** — Framework, công cụ dev, nền tảng (VD: React, Docker, AWS, TensorFlow, GitHub).
6. **job_titles** — Chức danh / vị trí tuyển dụng (VD: Lập trình viên, Data Scientist, DevOps Engineer, Product Manager).
7. **salary** — Mức lương nguyên văn (VD: "20-30 triệu", "thỏa thuận", "$2000-3000").
8. **events** — Sự kiện, hội nghị (VD: MWC 2026, Google I/O, CES 2026).
9. **locations** — Quốc gia, thành phố, khu vực (VD: Việt Nam, TP.HCM, Hà Nội, Silicon Valley).
10. **persons** — Tên người (lãnh đạo, chuyên gia, nhân vật được nhắc).
11. **laws** — Luật, nghị định, quy chuẩn (VD: Luật Trí tuệ nhân tạo, Luật AI 2025, GDPR).
12. **vulnerabilities** — Lỗ hổng bảo mật (VD: CVE-2025-12345, Log4Shell).

## QUY TẮC
- Trả về DUY NHẤT một mảng JSON hợp lệ, không bọc markdown (không ```json).
- Mỗi bài tương ứng đúng một object trong mảng; thứ tự object phải trùng thứ tự bài.
- Mỗi trường là mảng chuỗi; loại bỏ trùng lặp trong từng trường.
- Giữ tên entity đúng như xuất hiện trong văn bản gốc (tiếng Việt hoặc tiếng Anh).

## ĐỊNH DẠNG ĐẦU RA
[{"organizations":[],"products":[],"technologies":[],"programming_languages":[],"frameworks_tools":[],"job_titles":[],"salary":[],"events":[],"locations":[],"persons":[],"laws":[],"vulnerabilities":[]}, ...]"""


def _parse_entity_item(item: dict) -> dict:
    """Parse một object entity từ LLM, trả về dict đúng schema."""
    entity = empty_entities()
    for key in EMPTY_ENTITIES:
        val = item.get(key, [])
        entity[key] = list(val) if isinstance(val, list) else []
    return entity


def extract_batch_llm(articles: list[dict]) -> list[dict]:
    """
    Gửi batch bài lên Gemini, nhận về list entity dict.
    Tự retry nếu gặp lỗi 429/timeout. Response rỗng hoặc JSON lỗi: parse từng phần nếu có thể.
    """
    MAX_RETRIES = 5
    BASE_DELAY  = 10

    article_list = []
    for i, art in enumerate(articles):
        title = art.get("title", "")
        desc  = art.get("description", "")
        text  = f"{title}. {desc}".strip()
        article_list.append(f"{i + 1}. {text}")

    prompt = f"{SYSTEM_PROMPT}\n\nArticles:\n" + "\n\n".join(article_list)

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(model=MODEL, contents=prompt)
            raw = (response.text or "").strip()

            if not raw:
                print("    [WARN] API không trả về nội dung — dùng entity rỗng cho batch")
                return [empty_entities() for _ in articles]

            if raw.startswith("```"):
                parts = raw.split("```")
                if len(parts) >= 2:
                    raw = parts[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
            raw = raw.strip()

            parsed = json.loads(raw)

            if not isinstance(parsed, list):
                print(f"    [WARN] LLM không trả về array — dùng entity rỗng")
                return [empty_entities() for _ in articles]

            result = []
            for i, item in enumerate(parsed):
                if not isinstance(item, dict):
                    result.append(empty_entities())
                    continue
                result.append(_parse_entity_item(item))

            if len(result) != len(articles):
                print(f"    [WARN] LLM parse lệch ({len(result)} vs {len(articles)}) — bù entity rỗng cho thiếu")
                while len(result) < len(articles):
                    result.append(empty_entities())
                result = result[: len(articles)]

            return result

        except json.JSONDecodeError as e:
            print(f"    [WARN] JSON parse lỗi: {e} — thử parse từng object...")
            try:
                raw_trimmed = raw.strip()
                if raw_trimmed.startswith("["):
                    result = []
                    depth = 0
                    start = -1
                    for idx, c in enumerate(raw_trimmed):
                        if c in "[{":
                            if c == "{" and depth == 1:
                                start = idx
                            depth += 1
                        elif c in "]}":
                            if c == "}" and depth == 2 and start >= 0:
                                chunk = raw_trimmed[start : idx + 1]
                                obj = json.loads(chunk)
                                result.append(_parse_entity_item(obj))
                                start = -1
                            depth -= 1
                    if len(result) == len(articles):
                        return result
            except Exception:
                pass
            print("    [WARN] Không parse được — dùng entity rỗng cho batch")
            return [empty_entities() for _ in articles]

        except Exception as e:
            err_str = str(e)
            is_rate = "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower()
            is_retryable = is_rate or "timeout" in err_str.lower() or "503" in err_str
            if is_retryable and attempt < MAX_RETRIES - 1:
                wait = BASE_DELAY * (2 ** attempt)
                print(f"    [RATE LIMIT] Lần {attempt + 1}/{MAX_RETRIES} — chờ {wait}s...")
                time.sleep(wait)
            else:
                print(f"    [WARN] Lỗi API: {e} — dùng entity rỗng cho batch")
                return [empty_entities() for _ in articles]

    print(f"    [ERROR] Đã thử {MAX_RETRIES} lần vẫn lỗi — dùng entity rỗng")
    return [empty_entities() for _ in articles]


def make_batches(lst: list, size: int) -> list[list]:
    return [lst[i:i + size] for i in range(0, len(lst), size)]


# ==========================================
# HÀM XỬ LÝ FILE JSON
# ==========================================

def ner_json_file(input_path: str) -> str:
    print(f"\n{'=' * 55}")
    print(f"Đang xử lý: {os.path.basename(input_path)}")
    print(f"{'=' * 55}")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    posts = data.get("post_detail", [])
    total = len(posts)
    relevant_indices = [i for i, p in enumerate(posts) if p.get("is_relevant") is True]

    print(f"Tổng: {total} bài | Chỉ xử lý & ghi ra: {len(relevant_indices)} | "
          f"Bỏ qua (is_relevant=false): {total - len(relevant_indices)}")

    relevant_posts = [posts[i] for i in relevant_indices]
    batches        = make_batches(relevant_posts, BATCH_SIZE)
    total_batches  = len(batches)

    print(f"\n[Bước 1] Rule-based extract (offline)")
    print(f"  — Quét title + description bằng từ điển (ENTITY_DICT) và regex (CVE, lương, sự kiện...), không gọi API.")
    rule_results = []
    for post in relevant_posts:
        text = f"{post.get('title', '')}. {post.get('description', '')}".strip()
        rule_results.append(rule_based_extract(text))

    rb_count = sum(
        1 for r in rule_results
        if any(len(v) > 0 for v in r.values())
    )
    print(f"  — Số bài có ít nhất 1 entity từ từ điển/regex: {rb_count}/{len(relevant_posts)} bài.")

    # Luôn gọi LLM cho mọi bài (kết hợp dictionary + LLM, không skip)
    need_llm = list(range(len(relevant_posts)))
    llm_results = [empty_entities() for _ in relevant_posts]

    need_llm_posts   = [relevant_posts[i] for i in need_llm]
    need_llm_batches = make_batches(list(enumerate(need_llm_posts)), BATCH_SIZE)
    total_llm_batches = len(need_llm_batches)
    print(f"\n[Bước 2] LLM extract (mọi bài đều gọi LLM: {len(need_llm)} bài → {total_llm_batches} batch)...\n")

    api_results = []
    for batch_idx, batch in enumerate(need_llm_batches):
        _, batch_posts = zip(*batch)
        start = sum(len(b) for b in need_llm_batches[:batch_idx])
        end   = start + len(batch_posts)
        print(f"  Batch {batch_idx + 1}/{total_llm_batches} (bài {start + 1}–{end})...")

        llm_batch = extract_batch_llm(list(batch_posts))
        api_results.extend(llm_batch)

        if batch_idx < total_llm_batches - 1:
            time.sleep(DELAY)

    for local_idx, global_idx in enumerate(need_llm):
        llm_results[global_idx] = api_results[local_idx]

    print(f"\n[Bước 3] Merge + Normalize + Dedup...")
    all_entities = []
    for i, (rule, llm) in enumerate(zip(rule_results, llm_results)):
        merged = merge_entities(rule, llm)

        # Hậu xử lý salary: loại bỏ 'thỏa thuận' mơ hồ nếu không có ngữ cảnh tuyển dụng
        post = relevant_posts[i]
        post_title = post.get("title", "")
        post_desc  = post.get("description", "")
        postprocess_salary(merged, post_title, post_desc)

        all_entities.append(merged)

        post  = relevant_posts[i]
        title = post.get("title", "")[:45]
        orgs  = ", ".join(merged["organizations"][:3]) or "—"
        prods = ", ".join(merged["products"][:3]) or "—"
        techs = ", ".join(merged["technologies"][:3]) or "—"
        langs = ", ".join(merged["programming_languages"][:3]) or "—"
        print(f"  [{relevant_indices[i] + 1}] {title}")
        print(f"       ORG: {orgs} | PROD: {prods} | TECH: {techs} | LANG: {langs}")

    # Gán entities vào từng bài relevant
    for i, idx in enumerate(relevant_indices):
        posts[idx]["entities"] = all_entities[i]

    # Output chỉ giữ lại bài có is_relevant=true (đã có entities)
    output_posts = [posts[i] for i in relevant_indices]
    data_out = {k: v for k, v in data.items() if k != "post_detail"}
    data_out["post_detail"] = output_posts

    # Lưu output vào thư mục extracted_data với tên dạng extracted_data_XXX.json
    os.makedirs(EXTRACTED_DATA_DIR, exist_ok=True)
    base_name = os.path.basename(input_path)

    # Nếu input là filtered_data_XXX.json → output extracted_data_XXX.json
    if base_name.startswith("filtered_data_"):
        suffix = base_name[len("filtered_data_"):]
    # Hỗ trợ tên cũ: ner_XXX.json hoặc labeled_XXX.json nếu còn sót
    elif base_name.startswith("ner_"):
        suffix = base_name[len("ner_"):]
    elif base_name.startswith("labeled_"):
        suffix = base_name[len("labeled_"):]
    else:
        suffix = base_name

    output_filename = "extracted_data_" + suffix
    output_path = os.path.join(EXTRACTED_DATA_DIR, output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data_out, f, ensure_ascii=False, indent=2)

    print(f"\n  → Kết quả: {output_path} (chỉ {len(output_posts)} bài is_relevant=true)")
    return output_path


# ==========================================
# HÀM CHÍNH
# ==========================================

def main():
    global DIRECTORY

    parser = argparse.ArgumentParser(description="NER trích xuất entity cho bài IT (từ điển + LLM, mọi bài đều gọi LLM)")
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
    args = parser.parse_args()

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
        labeled_files = [os.path.abspath(f) for f in args.files]
        missing = [f for f in labeled_files if not os.path.exists(f)]
        if missing:
            for f in missing:
                print(f"[LỖI] Không tìm thấy file: {f}")
            sys.exit(1)
    else:
        # Fallback: scan DIRECTORY
        if not os.path.isdir(DIRECTORY):
            print(f"[LỖI] Thư mục không tồn tại: {DIRECTORY}")
            sys.exit(1)

        labeled_files = [
            os.path.join(DIRECTORY, f)
            for f in os.listdir(DIRECTORY)
            if f.startswith("filtered_data_") and f.endswith(".json")
        ]

    if not labeled_files:
        print(f"Không tìm thấy file đầu vào.")
        return

    print(f"Tìm thấy {len(labeled_files)} file:")
    for f in labeled_files:
        print(f"  - {os.path.basename(f)}")

    for file_path in labeled_files:
        ner_json_file(file_path)

    print(f"\n{'=' * 55}")
    print("Hoàn thành! Kiểm tra các file extracted_data_*.json trong thư mục extracted_data")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
