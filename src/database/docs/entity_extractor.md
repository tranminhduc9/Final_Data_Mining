# Entity Extractor Service

## Tổng Quan

Entity Extractor là service viết bằng **Python** chịu trách nhiệm trích xuất các thực thể (entities) từ dữ liệu thô. Sử dụng kết hợp:
- **PhoBERT/ELECTRA** - Model NER tiếng Việt (NlpHust/ner-vietnamese-electra-base)
- **Rule-based** - Regex patterns và dictionary cho các entity đặc thù

### Ưu Điểm Cách Tiếp Cận Này

| Đặc điểm | Lợi ích |
|----------|---------|
| **Không cần LLM** | Không cần API key, không tốn chi phí inference |
| **Model tiếng Việt** | ELECTRA fine-tuned cho tiếng Việt |
| **Rule-based bổ sung** | Dễ mở rộng dictionary công nghệ |
| **Xử lý text dài** | Sliding-window chunking cho văn bản > 512 tokens |
| **GPU Support** | Tự động sử dụng CUDA nếu có |

## Vị Trí Trong Pipeline

```
Kafka (raw_articles, raw_jobs)
         │
         ▼
┌─────────────────────────────────────┐
│        ENTITY EXTRACTOR             │
│          (Python)                   │
│                                     │
│  1. PhoBERT/ELECTRA NER             │
│     • ORG, PER, LOC                 │
│                                     │
│  2. Rule-based Extraction           │
│     • TECH (dictionary)             │
│     • DATE (regex)                  │
│     • JOB_ROLE (dictionary)         │
│     • SALARY (regex)                │
│                                     │
│  3. Normalize & Group               │
└─────────────┬───────────────────────┘
              │
              ▼
Kafka (extracted_articles, extracted_jobs)
```

## Các Loại Thực Thể Trích Xuất

### Entity Types

| Loại Entity | Label | Phương pháp | Ví dụ |
|-------------|-------|-------------|-------|
| **Person** | `PER` | ELECTRA NER | Nguyễn Văn A, CEO Tim Cook |
| **Organization** | `ORG` | ELECTRA NER | FPT, VNG, OpenAI |
| **Location** | `LOC` | ELECTRA NER | Hà Nội, TP.HCM, Việt Nam |
| **Technology** | `TECH` | Dictionary + Regex | Python, AI, Docker, Kubernetes |
| **Job Role** | `JOB_ROLE` | Dictionary + Regex | Senior Developer, CTO, Kỹ sư AI |
| **Salary** | `SALARY` | Regex Patterns | 15-25 triệu, $1,000-2,000 |
| **Date** | `DATE` | Regex Patterns | 14/05/2026, tháng 5/2026 |

## NER Model Configuration

### Model Setup

```python
from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline

NER_MODEL_NAME = "NlpHust/ner-vietnamese-electra-base"

_tokenizer = AutoTokenizer.from_pretrained(NER_MODEL_NAME)
_model = AutoModelForTokenClassification.from_pretrained(NER_MODEL_NAME)

ner_pipeline = pipeline(
    "ner",
    model=_model,
    tokenizer=_tokenizer,
    aggregation_strategy="simple",
    device=0 if torch.cuda.is_available() else -1,
)
```

### Xử Lý Text Dài (> 512 tokens)

```python
def _chunk_text_by_tokens(text: str, max_tokens: int = 480, overlap: int = 50) -> List[str]:
    """
    Chia text thành các chunk không vượt quá max_tokens.
    Các chunk liên tiếp overlap nhau để tránh bỏ sót entity tại biên.
    """
    token_ids = _tokenizer.encode(text, add_special_tokens=False)
    if len(token_ids) <= max_tokens:
        return [text]
    
    chunks = []
    start = 0
    while start < len(token_ids):
        end = min(start + max_tokens, len(token_ids))
        chunk_text = _tokenizer.decode(
            token_ids[start:end],
            skip_special_tokens=True,
        )
        chunks.append(chunk_text)
        if end >= len(token_ids):
            break
        start += max_tokens - overlap
    return chunks
```

## Từ Điển Công Nghệ (TECH)

### Case-Sensitive Abbreviations

```python
TECH_ABBREVS_CASE_SENSITIVE = {
    "AI", "IT", "RPA", "AGI", "NPU", "GPU", "TPU"
}
```

### Case-Insensitive Abbreviations

```python
TECH_ABBREVS = {
    "AWS", "GCP", "CSS", "PHP", "SQL", "VBA", "SAS",
    "API", "SDK", "IDE", "RPC", "ORM", "JWT", "SSH",
    "HTTP", "HTTPS", "REST", "SOAP", "HTML", "XML",
    "JSON", "YAML", "gRPC", "LLM", "GPT", "IoT", "WAF",
    "VPN", "ETL", "ERP", "CRM", "MES", "RAG", "NLP",
    # Cybersecurity & networking
    "DDoS", "MPC", "KYC", "SOC", "OTP", "2FA", "APK",
    "NFC", "ADB", "IPv4", "IPv6", "5G", "4G", "eSIM",
    # AI/ML
    "MLOps", "CI/CD", "OLAP", "DWH", "SIEM", "EDR",
}
```

### Tech Keywords

```python
TECH_KEYWORDS = [
    # AI & ML & Language Models
    "ChatGPT", "Claude", "Gemini", "Copilot", "Grok", "Perplexity", "DeepSeek",
    "OpenAI", "Anthropic", "Mistral", "Llama", "VinAI", "xAI",
    "Trí tuệ nhân tạo", "Machine Learning", "Deep Learning", "Generative AI",
    "GenAI", "AI tạo sinh", "Computer Vision", "AI Agent",
    
    # Programming Languages
    "Python", "Java", "JavaScript", "TypeScript", "Golang", "Rust",
    "Kotlin", "Swift", "Scala", "Ruby", "C++", "C#",
    
    # Frameworks
    "React", "Vue", "Angular", "Next.js", "Django", "FastAPI",
    "Spring Boot", "Express", "Flask", "Laravel", "Rails",
    
    # Databases
    "MySQL", "PostgreSQL", "MongoDB", "Redis", "Neo4j", "Elasticsearch",
    "Firebase", "Supabase", "BigQuery", "Redshift",
    
    # Cloud & DevOps
    "Docker", "Kubernetes", "AWS", "Azure", "Google Cloud",
    "Jenkins", "Terraform", "Ansible", "Prometheus", "Grafana",
    
    # AI/ML Libraries
    "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "Pandas", "NumPy",
    "Transformers", "HuggingFace", "LangChain", "LlamaIndex",
    
    # Big Data
    "Apache Spark", "Apache Kafka", "Apache Airflow", "Hadoop",
    "Snowflake", "Databricks", "dbt",
]
```

## Regex Patterns

### Date Patterns

```python
DATE_PATTERNS = [
    # Tiếng Việt
    r"\b(ng[aà]y\s+\d{1,2}\s+th[aá]ng\s+\d{1,2}(?:\s+n[aă]m\s+\d{4})?)\b",
    r"\b(th[aá]ng\s+\d{1,2}(?:\s+n[aă]m\s+\d{4})?)\b",
    r"\b(Qu[yý]\s+(?:I{1,3}|IV|[1-4])(?:\s*/\s*\d{4})?)\b",
    
    # Numeric formats
    r"\b(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})\b",
    r"(?<!\d[/\-])(\d{1,2}[/\-]\d{4})(?!\d)",
    
    # English
    r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})\b",
]
```

### Salary Patterns

```python
SALARY_PATTERNS = [
    # Vietnamese format: "X - Y triệu"
    r"\b(\d+(?:[,.]\d+)?\s*[-–]\s*\d+(?:[,.]\d+)?\s*tri[eệ]u)\b",
    r"\b(\d+(?:[,.]\d+)?\s*tri[eệ]u(?:\s*VNĐ|\s*VND)?)\b",
    
    # "từ X đến Y triệu"
    r"\b(t[ừu]\s+\d+(?:[,.]\d+)?(?:\s*đến\s+\d+(?:[,.]\d+)?)?\s*tri[eệ]u)\b",
    
    # USD format
    r"(\$\d{1,3}(?:,\d{3})*(?:\s*[-–]\s*\$\d{1,3}(?:,\d{3})*)?)",
    
    # Negotiable
    r"\b(lương\s+(?:thương lượng|cạnh tranh|thoả thuận))\b",
    r"\b(salary\s+(?:negotiable|competitive))\b",
]
```

### Job Role Keywords

```python
JOB_ROLE_KEYWORDS = [
    # Management
    "CEO", "CTO", "CIO", "CPO", "CDO", "COO", "CFO",
    "Chief Executive Officer", "Chief Technology Officer",
    "Giám đốc điều hành", "Giám đốc công nghệ", "Trưởng phòng",
    
    # Engineering
    "Software Engineer", "Senior Software Engineer", "Full Stack Developer",
    "Frontend Developer", "Backend Developer", "DevOps Engineer",
    "AI Engineer", "ML Engineer", "Data Scientist", "Data Engineer",
    
    # Vietnamese
    "Kỹ sư phần mềm", "Lập trình viên", "Kỹ sư AI", "Kỹ sư dữ liệu",
    "Chuyên viên phân tích dữ liệu", "Kiến trúc sư phần mềm",
]
```

## Xử Lý Dữ Liệu

### Extract Entities Function

```python
def extract_entities_ner(text: str) -> List[dict]:
    """
    Chạy NER model trên text, đồng thời bổ sung DATE/TECH/JOB_ROLE/SALARY.
    
    Returns:
        List[dict]: [{"entity": "Python", "label": "TECH", "score": 1.0}, ...]
    """
    if not text.strip():
        return []
    
    # 1. Chia text thành chunks nếu vượt giới hạn 512 tokens
    chunks = _chunk_text_by_tokens(text, max_tokens=480, overlap=50)
    
    # 2. Chạy NER trên từng chunk, dedup theo (word.lower(), label)
    final_entities = []
    _ner_seen = set()
    
    for chunk in chunks:
        ner_results = ner_pipeline(chunk)
        for ent in ner_results:
            label = ent.get("entity_group", "").upper()
            word = ent.get("word", "").strip()
            score = ent.get("score", 0)
            
            dedup_key = (word.lower(), label)
            if dedup_key not in _ner_seen:
                _ner_seen.add(dedup_key)
                final_entities.append({
                    "entity": word,
                    "label": label,
                    "score": round(float(score), 2),
                })
    
    # 3. Rule-based extraction
    final_entities.extend(extract_date_entities(text))
    final_entities.extend(extract_tech_entities(text))
    final_entities.extend(extract_job_role_entities(text))
    final_entities.extend(extract_salary_entities(text))
    
    return final_entities
```

### Group Entities

```python
def group_entities(flat_entities: List[dict]) -> dict:
    """
    Chuyển danh sách entities phẳng sang dict có cấu trúc:
    {
        "PER": [...],
        "ORG": [...],
        "LOC": [...],
        "DATE": [...],
        "TECH": [...],
        "JOB_ROLE": [...],
        "SALARY": [...]
    }
    """
    result = {
        "PER": [], "ORG": [], "LOC": [],
        "DATE": [], "TECH": [], "JOB_ROLE": [], "SALARY": [],
    }
    seen = {k: set() for k in result}
    
    for ent in flat_entities:
        label = ent.get("label", "").upper()
        value = normalize_entity(ent.get("entity", ""), label)
        
        if label in result and value and value not in seen[label]:
            seen[label].add(value)
            result[label].append(value)
    
    return result
```

## Output Format

### Extracted Article

```json
{
    "source_platform": "VNExpress",
    "scraped_at": "2026-05-14T15:00:00Z",
    "post_detail": [
        {
            "title": "OpenAI ra mắt GPT-5",
            "content": "Nội dung bài viết...",
            "is_relevant": true,
            "entities": {
                "PER": ["Sam Altman"],
                "ORG": ["OpenAI"],
                "LOC": ["Mỹ"],
                "TECH": ["OpenAI", "GPT-5", "AI", "LLM"],
                "DATE": ["14/05/2026"],
                "JOB_ROLE": [],
                "SALARY": []
            }
        }
    ]
}
```

### Extracted Job

```json
{
    "source_platform": "TopCV",
    "post_detail": [
        {
            "job_title": "Senior AI Engineer",
            "job_description": "Mô tả công việc...",
            "is_relevant": true,
            "entities": {
                "PER": [],
                "ORG": ["FPT"],
                "LOC": ["Hà Nội"],
                "TECH": ["Python", "TensorFlow", "PyTorch", "AI"],
                "DATE": [],
                "JOB_ROLE": ["Senior AI Engineer", "AI Engineer"],
                "SALARY": ["25-40 triệu"]
            }
        }
    ]
}
```

## Performance

| Metric | Value |
|--------|-------|
| **Language** | Python 3.10+ |
| **Model** | NlpHust/ner-vietnamese-electra-base |
| **GPU** | Optional (CUDA auto-detect) |
| **Throughput** | ~100 articles/min (CPU) |
| **Memory** | ~2GB (model + overhead) |
| **Max Tokens** | 512 (auto-chunking for longer texts) |

## Dependencies

```txt
# requirements.txt
transformers>=4.30.0
torch>=2.0.0
kafka-python>=2.0.2
```

## Hình Ảnh Minh Họa

> **Ghi chú:** Thêm ảnh entity extraction flow tại đây
> 
> ![Entity Extraction Flow](./images/entity_extraction_flow.png)
> *Hình 1: Quy trình trích xuất thực thể với PhoBERT/ELECTRA*

> **Ghi chú:** Thêm ảnh entity types diagram tại đây
> 
> ![Entity Types](./images/entity_types.png)
> *Hình 2: Các loại thực thể được trích xuất*