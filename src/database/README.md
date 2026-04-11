# 📚 src/database - Neo4j Graph Database Module

## 🎯 Mục Đích
Module quản lý **chuyển đổi** dữ liệu tin tức sang **Job Market Graph Schema** và **import** vào **Neo4j Aura**.

---

## 📂 Cấu Trúc Thư Mục

```
src/database/
├── __init__.py                 # Package marker
├── requirements.txt            # Dependencies
├── README.md                   # Documentation 
│
└── utils/                      # ⭐ NEW: Job Market transformation & import
    ├── schema_define.py        # 1️⃣ Job Market Schema definitions
    ├── data_transform.py       # 2️⃣ News → Job Schema transformer
    ├── database_connection.py  # 3️⃣ Neo4j importer (v2)
    ├── neo4j_config.py         # Config loader
    ├── run_script.py           # 4️⃣ Main pipeline orchestrator
    └── note.md                 # Implementation notes
```

---

## 🏗️ Core Components

### 1. **`utils/schema_define.py`** - Job Market Schema Definitions

**6 Node Types:**

| Node | Properties | Ví Dụ |
|------|-----------|-------|
| **Article** | title, content, source, published_date, sentiment_score | "OpenAI ra mắt GPT-5" từ VN-Express |
| **Technology** | name, category, description, trend_score | "AI" (Category: AI), "Python" (Category: Backend) |
| **Company** | name, industry, size, location, rating | "OpenAI" (Tech industry, SF location) |
| **Job** | title, salary_min/max, level, source_url, posted_date | "Senior AI Engineer" |
| **Skill** | name, category, demand_score | "Python" (Category: Programming) |
| **Person** | name, role | "Sam Altman" (Role: CEO) |

**Relationship Types:**
- `MENTIONS` - Article → Technology/Company
- `USES` - Company → Technology
- `REQUIRES` - Job → Skill
- `POSTED_BY` - Job → Company
- `WORKS_AT` - Person → Company
- `WROTE` - Person → Article
- `RELATED_TO` - Technology → Technology

---

### 2. **`utils/data_transform.py`** - Data Transformation Pipeline

**Transform News → Job Market Schema:**

```
Raw News Data (JSON)
    ↓
Extract Entities (Organizations, Technologies, Persons)
    ↓
Auto-detect Technology Categories (AI, Cloud, DevOps, etc.)
    ↓
Calculate Sentiment Score (-1 to 1)
    ↓
Extract Person Roles (CEO, CTO, Engineer, etc.)
    ↓
Deduplicate & Structure into Job Schema
    ↓
Export to JSON
```

**Tính Năng:**

✅ **Auto Tech Categorization:**
- AI: AI, Machine Learning, GPT, LLM, NLP
- Cloud: AWS, Azure, Docker, Kubernetes
- DevOps: CI/CD, Jenkins, Terraform, Ansible
- Frontend: React, Vue, Angular, JavaScript
- Backend: Python, Java, Node.js, Go
- Database: SQL, MongoDB, PostgreSQL, Redis
- Mobile: iOS, Android, Flutter
- Data: Analytics, Spark, Hadoop

✅ **Sentiment Analysis:**
- Positive keywords: tăng, tốt, thành công, đột phá
- Negative keywords: giảm, xấu, thất bại, rủi ro

✅ **Role Extraction:**
- CEO, CTO, Founder, Engineer, Researcher, Manager

✅ **Deduplication:**
- Dùng Set để loại bỏ duplicates
- Case-insensitive matching

---

### 3. **`utils/database_connection.py`** - Neo4j Importer (v2)

**Main Methods:**

| Method | Purpose |
|--------|---------|
| `connect()` | Kết nối Neo4j Aura |
| `create_constraints_and_indexes()` | Tạo unique constraints & indexes |
| `import_articles()` | Import Article nodes |
| `import_technologies()` | Import Technology nodes |
| `import_companies()` | Import Company nodes |
| `import_persons()` | Import Person nodes |
| `import_skills()` | Import Skill nodes |
| `create_article_mentions_relationships()` | Tạo MENTIONS relationships |
| Nhiều create nữa ...| Tạo relationship|
| `get_statistics()` | Lấy node & relationship statistics |


---

### 4. **`utils/run_script.py`** - Main Pipeline Orchestrator

**Full workflow:**

```python
# 1. Transform news data to Job Market schema
transformer = DataTransformer()
transformer.batch_transform(DATA_PATH_VNEP)
transformer.batch_transform(DATA_PATH_DT)
transformer.export_to_json()

# 2. Import to Neo4j
importer = Neo4jJobImporter(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
importer.connect()
importer.create_constraints_and_indexes()

# 3. Import nodes
importer.import_articles(transformer.articles)
importer.import_technologies(list(transformer.technologies))
importer.import_companies(list(transformer.companies))
importer.import_persons(list(transformer.persons))
importer.import_skills(list(transformer.skills))

# 4. Create relationships
importer.create_article_mentions_relationships(transformer)

# 5. Print results
stats = importer.get_statistics()
importer.disconnect()
```

**Chạy:**
```bash
cd src/database/utils
python run_script.py
```

---

### 5. **`neo4j_config.py`** - Configuration

Load từ `.env`:

```python
NEO4J_URI          # "neo4j+s://xxx.databases.neo4j.io"
NEO4J_USERNAME     # "neo4j"
NEO4J_PASSWORD     # Your password
NEO4J_DATABASE     # "neo4j"
BATCH_SIZE         # 100 (for batch operations)
DATA_PATH_VNEP     # Path to VN-Express data
DATA_PATH_DT       # Path to Dân Trí data
```

---

# TỪ DƯỚI NÀY KHÔNG CẦN QUAN TÂM

---

## 🚀 Quick Start


### Expected Output

```
============================================================
DATA TRANSFORMATION & NEO4J IMPORT PIPELINE
============================================================

📊 STEP 1: TRANSFORMING DATA
VN-Express: 40 articles
Dân Trí: 23 articles

╔════════════════════════════════════════╗
║   DATA TRANSFORMATION SUMMARY           ║
╚════════════════════════════════════════╝
📊 Articles:      63
🔧 Technologies: 22
🏢 Companies:     35
👤 Persons:       9
💡 Skills:        22

🗄️ STEP 2: IMPORTING TO NEO4J
✅ Connected to Neo4j Aura
✅ All constraints and indexes created
✅ Imported 63 articles
✅ Imported 22 technologies
✅ Imported 35 companies
✅ Imported 9 persons
✅ Imported 22 skills
✅ Created 200+ MENTIONS relationships

📈 IMPORT STATISTICS
Article:      63
Technology:   22
Company:      35
Skill:        22
Person:       9
Relationships: 332

✅ PIPELINE COMPLETED SUCCESSFULLY!
```

---

## 📊 Data Flow Diagram

```
VN-Express.json                  Dân Trí.json
        ↓                              ↓
    [Extract Entities] ← ← ← ← ← ← ← ←
        ↓
    [Transform to Job Schema]
        ├─ Article nodes
        ├─ Technology nodes (with auto-categorization)
        ├─ Company nodes
        ├─ Person nodes (with role extraction)
        └─ Skill nodes
        ↓
    [Export to JSON]
        ↓
    [Neo4j Importer]
        ├─ Create constraints & indexes
        ├─ Import all nodes
        └─ Create MENTIONS relationships
        ↓
    [Neo4j Aura Database]
        ├─ 63 Articles
        ├─ 35 Companies
        ├─ 22 Technologies
        ├─ 9 Persons
        ├─ 22 Skills
        └─ 332 Relationships
```

---

## 🔍 Verification

Kiểm tra dữ liệu import thành công:

```python
from utils.database_connection import Neo4jJobImporter
from utils.neo4j_config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

importer = Neo4jJobImporter(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
importer.connect()

# Get statistics
stats = importer.get_statistics()
print(f"Articles: {stats['Article']}")
print(f"Companies: {stats['Company']}")
print(f"Relationships: {stats['Relationships']}")

importer.disconnect()
```

Hoặc dùng Neo4j Browser:
```cypher
# Count all nodes
MATCH (n) RETURN labels(n) as label, count(n) as count

# Check relationships
MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count
```

---

## 📦 Dependencies

```
neo4j              # Neo4j Python driver
python-dotenv      # Load environment variables
pandas             # Data processing
numpy              # Numerical operations
colorlog           # Colored logging
```

---

## 🎯 Use Cases

### 1. **Analyze Technology Trends**
```cypher
MATCH (t:Technology)<-[:MENTIONS]-(a:Article)
WHERE a.published_date > date('2026-03-01')
RETURN t.name, t.category, count(a) as trend_score
ORDER BY trend_score DESC
```

### 2. **Find Company Relationships**
```cypher
MATCH (c1:Company)<-[:MENTIONS]-(a:Article)-[:MENTIONS]->(c2:Company)
WHERE c1.name < c2.name
RETURN c1.name, c2.name, count(a) as co_mentions
LIMIT 20
```

### 3. **Extract Job Market Insights**
```cypher
MATCH (j:Job)-[:REQUIRES]->(s:Skill)
RETURN s.name, s.category, count(j) as job_count
ORDER BY job_count DESC
LIMIT 20
```

### 4. **Sentiment Analysis**
```cypher
MATCH (a:Article)-[:MENTIONS]->(c:Company)
RETURN c.name, avg(a.sentiment_score) as avg_sentiment, count(a) as mentions
ORDER BY avg_sentiment DESC
```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'neo4j'` | `pip install neo4j` |
| `Neo4j connection refused` | Check URI, username, password |
| `Database not found` | Verify database name in .env |
| `No orphaned nodes found` | All nodes properly connected ✅ |
| `Duplicate key constraint violation` | Check for duplicate articles in source |

---

## 📚 Related Files

- **Config:** [neo4j_config.py](neo4j_config.py)
- **Legacy Importer:** [neo4j_importer.py](neo4j_importer.py)
- **Query Examples:** [query_examples.py](query_examples.py)
- **Root Config:** [../../.env.example](../../.env.example)

---

## ✨ Summary

| Component | Purpose | Status |
|-----------|---------|--------|
| V1 Importer (neo4j_importer.py) | News articles schema | ⚠️ Legacy |
| V2 Transformer (utils/data_transform.py) | News → Job schema | ✅ Active |
| V2 Importer (utils/database_connection.py) | Neo4j import | ✅ Active |
| Pipeline (utils/run_script.py) | Orchestration | ✅ Active |
| Schema (utils/schema_define.py) | Type definitions | ✅ Active |

**Latest Status:** Ready for Job Market Graph Analysis! 🚀

---

**Created:** March 2026  
**Version:** 2.0 (Job Market Schema)  
**Last Updated:** March 14, 2026
