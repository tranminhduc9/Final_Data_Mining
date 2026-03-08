"""
==========================================================
  SCRIPT TRÍCH XUẤT THỰC THỂ (NER) - HYBRID
  Chiến lược: Rule-based + Dictionary → LLM → Merge
==========================================================

HƯỚNG DẪN:
  python ner_articles.py

Input:  labeled_*.json  (chỉ xử lý bài is_relevant=true)
Output: ner_*.json      (thêm trường "entities" vào mỗi bài)

PIPELINE:
  1. Rule-based extract  → bắt entity đã biết (offline, miễn phí)
  2. LLM extract         → bắt entity mới, ngữ cảnh, persons, events
  3. Merge + Normalize   → gộp kết quả, chuẩn hóa tên entity
  4. Save JSON
"""

import argparse
import json
import os
import re
import sys
import time

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ==========================================
# CẤU HÌNH
# ==========================================

API_KEY    = "" #Dán API Key
DIRECTORY  = r"C:\Users\Admin\MyProject\ScrapeData"
MODEL      = "gemini-2.0-flash"
BATCH_SIZE = 5
DELAY      = 4.0
LLM_MIN_FIELDS = 3   # Bài có < N loại entity từ rule-based mới gọi LLM

if API_KEY == "YOUR_API_KEY_HERE":
    print("=" * 55)
    print("  LỖI: Chưa điền API Key!")
    print("  Truy cập: https://aistudio.google.com/apikey")
    print("=" * 55)
    sys.exit(1)

try:
    from google import genai
except ImportError:
    print("LỖI: pip install google-genai")
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

    # Products
    "chatgpt":     ("products", "ChatGPT"),
    "claude":      ("products", "Claude"),
    "gemini":      ("products", "Gemini"),
    "copilot":     ("products", "Copilot"),
    "grok":        ("products", "Grok"),
    "llama":       ("products", "Llama"),

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

    # Laws
    "luật trí tuệ nhân tạo":   ("laws", "Luật Trí tuệ nhân tạo 2025"),
    "luật ai":                  ("laws", "Luật AI 2025"),
    "gdpr":                     ("laws", "GDPR"),
    "luật an ninh mạng":        ("laws", "Luật An ninh mạng"),
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
        r"\d+[-–]\d+\s*triệu(?:\s*đồng)?",     # 20-30 triệu
        r"\$\s*\d+(?:[.,]\d+)?[-–]\$?\s*\d+",   # $2000-3000
        r"(?:lương\s+)?(?:từ\s+)?\d+\+?\s*triệu", # 25 triệu / 25+ triệu
        r"thỏa thuận",                            # Thỏa thuận
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


def rule_based_extract(text: str) -> dict[str, list[str]]:
    """
    Trích xuất entity từ text bằng dictionary lookup và regex.
    Trả về dict cùng schema với EMPTY_ENTITIES.
    """
    result: dict[str, list[str]] = {k: [] for k in EMPTY_ENTITIES}
    text_lower = text.lower()

    # 1. Dictionary lookup
    for term, (field, display) in ENTITY_DICT.items():
        if term in text_lower:
            if display not in result[field]:
                result[field].append(display)

    # 2. Regex patterns
    for field, patterns in REGEX_PATTERNS.items():
        for pattern in patterns:
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            for m in matches:
                m = m.strip()
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
# LLM EXTRACTION
# ==========================================

SYSTEM_PROMPT = """You are a Named Entity Recognition (NER) expert for Vietnamese IT content.

Extract named entities from each article and return a JSON array (same order as input).
Focus on entities NOT easily found by pattern matching: persons, new products, events, laws, context-dependent entities.

Fields (return ALL 12, empty array [] if none found):
- organizations: company/institution names
- products: software/hardware product names
- technologies: broad technology terms (AI, 5G, cloud...)
- programming_languages: coding languages only (Python, Java...)
- frameworks_tools: frameworks, dev tools (React, Docker...)
- job_titles: job roles (AI Engineer, Senior Backend...)
- salary: salary as raw strings ("20-30 triệu", "$2000")
- events: conferences, events (MWC 2026, Google I/O...)
- locations: countries, cities
- persons: people's names
- laws: laws, regulations (Luật AI 2025, GDPR...)
- vulnerabilities: security vulns (CVE-xxxx, Log4Shell...)

RULES:
- Return ONLY valid JSON array, no markdown
- Remove duplicates
- Keep entity names as they appear in the original Vietnamese text

Format:
[{"organizations":[],"products":[],"technologies":[],"programming_languages":[],"frameworks_tools":[],"job_titles":[],"salary":[],"events":[],"locations":[],"persons":[],"laws":[],"vulnerabilities":[]}, ...]"""


def extract_batch_llm(articles: list[dict]) -> list[dict]:
    """
    Gửi batch bài lên Gemini, nhận về list entity dict.
    Tự retry nếu gặp lỗi 429.
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
            raw = response.text.strip()

            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            parsed = json.loads(raw)

            if not isinstance(parsed, list) or len(parsed) != len(articles):
                print(f"    [WARN] LLM parse lệch ({len(parsed)} vs {len(articles)}) — dùng entity rỗng")
                return [dict(EMPTY_ENTITIES) for _ in articles]

            result = []
            for item in parsed:
                entity = {}
                for key in EMPTY_ENTITIES:
                    val = item.get(key, [])
                    entity[key] = val if isinstance(val, list) else []
                result.append(entity)

            return result

        except json.JSONDecodeError as e:
            print(f"    [WARN] JSON parse lỗi: {e} — dùng entity rỗng")
            return [dict(EMPTY_ENTITIES) for _ in articles]

        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower():
                wait = BASE_DELAY * (2 ** attempt)
                print(f"    [RATE LIMIT] Lần {attempt + 1}/{MAX_RETRIES} — chờ {wait}s...")
                time.sleep(wait)
            else:
                print(f"    [WARN] Lỗi API: {e} — dùng entity rỗng")
                return [dict(EMPTY_ENTITIES) for _ in articles]

    print(f"    [ERROR] Đã thử {MAX_RETRIES} lần vẫn lỗi — dùng entity rỗng")
    return [dict(EMPTY_ENTITIES) for _ in articles]


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

    print(f"Tổng: {total} bài | Xử lý: {len(relevant_indices)} | "
          f"Bỏ qua (not relevant): {total - len(relevant_indices)}")

    # Bài không liên quan → entities rỗng
    for i, post in enumerate(posts):
        if i not in relevant_indices:
            post["entities"] = dict(EMPTY_ENTITIES)

    relevant_posts = [posts[i] for i in relevant_indices]
    batches        = make_batches(relevant_posts, BATCH_SIZE)
    total_batches  = len(batches)

    print(f"\n[Bước 1] Rule-based extract (offline)...")
    rule_results = []
    for post in relevant_posts:
        text = f"{post.get('title', '')}. {post.get('description', '')}".strip()
        rule_results.append(rule_based_extract(text))

    rb_count = sum(
        1 for r in rule_results
        if any(len(v) > 0 for v in r.values())
    )
    print(f"  → {rb_count}/{len(relevant_posts)} bài có entity từ rule-based")

    # Phân loại: bài nào cần gọi LLM (rule-based chưa đủ LLM_MIN_FIELDS loại entity)
    need_llm   = [i for i, r in enumerate(rule_results)
                  if sum(1 for v in r.values() if v) < LLM_MIN_FIELDS]
    skip_llm   = [i for i in range(len(relevant_posts)) if i not in need_llm]

    print(f"  → Gọi LLM: {len(need_llm)} bài | Skip (rule-based đủ ≥{LLM_MIN_FIELDS} loại): {len(skip_llm)} bài")

    # Khởi tạo llm_results rỗng cho tất cả
    llm_results = [dict(EMPTY_ENTITIES) for _ in relevant_posts]

    if need_llm:
        need_llm_posts   = [relevant_posts[i] for i in need_llm]
        need_llm_batches = make_batches(list(enumerate(need_llm_posts)), BATCH_SIZE)
        total_llm_batches = len(need_llm_batches)
        print(f"\n[Bước 2] LLM extract ({len(need_llm)} bài → {total_llm_batches} batch)...\n")

        api_results = []
        for batch_idx, batch in enumerate(need_llm_batches):
            _, batch_posts = zip(*batch)
            start = batch_idx * BATCH_SIZE
            end   = start + len(batch_posts)
            print(f"  Batch {batch_idx + 1}/{total_llm_batches} (bài cần LLM {start + 1}–{end})...")

            llm_batch = extract_batch_llm(list(batch_posts))
            api_results.extend(llm_batch)

            if batch_idx < total_llm_batches - 1:
                time.sleep(DELAY)

        for local_idx, global_idx in enumerate(need_llm):
            llm_results[global_idx] = api_results[local_idx]
    else:
        print(f"\n[Bước 2] LLM bỏ qua hoàn toàn — rule-based đã đủ cho tất cả bài!")

    print(f"\n[Bước 3] Merge + Normalize + Dedup...")
    all_entities = []
    for i, (rule, llm) in enumerate(zip(rule_results, llm_results)):
        merged = merge_entities(rule, llm)
        all_entities.append(merged)

        post  = relevant_posts[i]
        title = post.get("title", "")[:45]
        orgs  = ", ".join(merged["organizations"][:3]) or "—"
        prods = ", ".join(merged["products"][:3]) or "—"
        techs = ", ".join(merged["technologies"][:3]) or "—"
        langs = ", ".join(merged["programming_languages"][:3]) or "—"
        print(f"  [{relevant_indices[i] + 1}] {title}")
        print(f"       ORG: {orgs} | PROD: {prods} | TECH: {techs} | LANG: {langs}")

    # Gán entities vào posts
    for i, idx in enumerate(relevant_indices):
        posts[idx]["entities"] = all_entities[i]

    # Lưu output
    dir_name    = os.path.dirname(input_path)
    base_name   = os.path.basename(input_path)
    clean_name  = base_name.replace("labeled_", "", 1)
    output_path = os.path.join(dir_name, "ner_" + clean_name)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n  → Kết quả: {output_path}")
    return output_path


# ==========================================
# HÀM CHÍNH
# ==========================================

def main():
    parser = argparse.ArgumentParser(description="NER trích xuất entity cho bài IT")
    parser.add_argument(
        "files", nargs="*",
        help="Đường dẫn file labeled_*.json cần xử lý. "
             "Nếu bỏ trống, tự scan thư mục DIRECTORY."
    )
    args = parser.parse_args()

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
        labeled_files = [
            os.path.join(DIRECTORY, f)
            for f in os.listdir(DIRECTORY)
            if f.startswith("labeled_") and f.endswith(".json")
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
    print("Hoàn thành! Kiểm tra các file ner_*.json")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
