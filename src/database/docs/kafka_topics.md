# Kafka Topics Configuration

## Tổng Quan

Apache Kafka đóng vai trò là **message broker** trung tâm trong hệ thống, kết nối các thành phần thông qua cơ chế publish/subscribe. Kafka đảm bảo:
- Xử lý dữ liệu thời gian thực
- Tách biệt các service
- Khả năng mở rộng cao
- Độ tin cậy và durability

## Kafka Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         KAFKA CLUSTER                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        TOPICS                                        │   │
│  │                                                                      │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │   │
│  │  │  raw_articles   │  │   raw_jobs      │  │ extracted_      │     │   │
│  │  │                 │  │                 │  │   articles      │     │   │
│  │  │  Partitions: 3  │  │  Partitions: 3  │  │  Partitions: 3  │     │   │
│  │  │  Replication: 1 │  │  Replication: 1 │  │  Replication: 1 │     │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘     │   │
│  │                                                                      │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │   │
│  │  │  extracted_jobs │  │ article_vectors │  │   job_vectors   │     │   │
│  │  │                 │  │                 │  │                 │     │   │
│  │  │  Partitions: 3  │  │  Partitions: 3  │  │  Partitions: 3  │     │   │
│  │  │  Replication: 1 │  │  Replication: 1 │  │  Replication: 1 │     │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘     │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     CONSUMER GROUPS                                  │   │
│  │                                                                      │   │
│  │  • entity-extractor        (Entity Extractor Service)               │   │
│  │  • embedding-service       (Embedding Service)                      │   │
│  │  • neo4j-writer           (Neo4j Writer Service)                    │   │
│  │  • qdrant-writer          (Qdrant Writer Service)                   │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Topics Overview

| Topic | Producer | Consumer | Mô tả |
|-------|----------|----------|-------|
| `raw_articles` | Crawlers | Entity Extractor | Bài viết thô từ crawler |
| `raw_jobs` | Crawlers | Entity Extractor | Job postings thô từ crawler |
| `extracted_articles` | Entity Extractor | Neo4j Writer, Embedding Service | Bài viết đã trích xuất entities |
| `extracted_jobs` | Entity Extractor | Neo4j Writer, Embedding Service | Jobs đã trích xuất entities |
| `article_vectors` | Embedding Service | Qdrant Writer | Vector embeddings của articles |
| `job_vectors` | Embedding Service | Qdrant Writer | Vector embeddings của jobs |

## Chi Tiết Từng Topic

### 1. raw_articles

**Mô tả:** Nhận bài viết thô từ các crawlers (VNExpress, GenK, DanTri).

**Producer:** Crawlers (Python)

**Consumer:** Entity Extractor (Golang)

**Message Schema:**

```json
{
    "message_type": "article",
    "source_platform": "VNExpress",
    "crawled_at": "2026-05-14T15:00:00Z",
    "data": {
        "title": "OpenAI ra mắt GPT-5",
        "publish_date": "2026-05-14",
        "content": "Nội dung bài viết...",
        "source_url": "https://vnexpress.net/..."
    }
}
```

**Key:** MD5 hash của `source_url`

---

### 2. raw_jobs

**Mô tả:** Nhận job postings thô từ crawlers (TopCV).

**Producer:** Crawlers (Python)

**Consumer:** Entity Extractor (Golang)

**Message Schema:**

```json
{
    "message_type": "job",
    "source_platform": "TopCV",
    "crawled_at": "2026-05-14T15:00:00Z",
    "data": {
        "job_title": "Senior AI Engineer",
        "company_name": "FPT",
        "location": "Hà Nội",
        "salary": "25-40 triệu",
        "level": "Senior",
        "description": "Mô tả công việc...",
        "requirement": "Yêu cầu...",
        "benefit": "Quyền lợi...",
        "skills": ["Python", "TensorFlow"],
        "source_url": "https://topcv.vn/...",
        "posted_date": "2026-05-14"
    }
}
```

**Key:** MD5 hash của `source_url`

---

### 3. extracted_articles

**Mô tả:** Bài viết đã được trích xuất entities bởi Entity Extractor.

**Producer:** Entity Extractor (Golang)

**Consumer:** 
- Neo4j Writer (Golang)
- Embedding Service (Python)

**Message Schema:**

```json
{
    "message_type": "extracted_article",
    "source_platform": "VNExpress",
    "crawled_at": "2026-05-14T15:00:00Z",
    "extracted_at": "2026-05-14T15:01:00Z",
    "data": {
        "title": "OpenAI ra mắt GPT-5",
        "publish_date": "2026-05-14",
        "content": "Nội dung bài viết...",
        "source_url": "https://vnexpress.net/...",
        "entities": {
            "TECH": ["OpenAI", "GPT-5", "AI"],
            "ORG": ["OpenAI"],
            "LOC": ["Mỹ"],
            "DATE": ["14/05/2026"],
            "JOB_ROLE": [],
            "SALARY": []
        }
    }
}
```

**Key:** MD5 hash của `source_url`

---

### 4. extracted_jobs

**Mô tả:** Job postings đã được trích xuất entities.

**Producer:** Entity Extractor (Golang)

**Consumer:**
- Neo4j Writer (Golang)
- Embedding Service (Python)

**Message Schema:**

```json
{
    "message_type": "extracted_job",
    "source_platform": "TopCV",
    "crawled_at": "2026-05-14T15:00:00Z",
    "extracted_at": "2026-05-14T15:01:00Z",
    "data": {
        "job": {
            "title": "Senior AI Engineer",
            "description": "...",
            "requirement": "...",
            "benefit": "...",
            "salary": "25-40 triệu",
            "source_url": "https://topcv.vn/..."
        },
        "company": {
            "name": "FPT",
            "location": "Hà Nội"
        },
        "skills": ["Python", "TensorFlow"],
        "technologies": ["Python", "TensorFlow", "PyTorch", "AI"],
        "entities": {
            "TECH": ["Python", "TensorFlow", "AI"],
            "ORG": ["FPT"],
            "LOC": ["Hà Nội"],
            "SALARY": ["25-40 triệu"],
            "JOB_ROLE": ["Senior AI Engineer"]
        }
    }
}
```

**Key:** MD5 hash của `source_url`

---

### 5. article_vectors

**Mô tả:** Vector embeddings của articles từ Embedding Service.

**Producer:** Embedding Service (Python)

**Consumer:** Qdrant Writer (Golang)

**Message Schema:**

```json
{
    "message_type": "article_vector",
    "id": "abc123def456",
    "source_url": "https://vnexpress.net/...",
    "source_platform": "VNExpress",
    "embedding": [0.123, 0.456, ...],  // 768 dimensions
    "metadata": {
        "title": "OpenAI ra mắt GPT-5",
        "published_date": "2026-05-14"
    }
}
```

**Key:** Article ID (MD5 hash)

---

### 6. job_vectors

**Mô tả:** Vector embeddings của job postings.

**Producer:** Embedding Service (Python)

**Consumer:** Qdrant Writer (Golang)

**Message Schema:**

```json
{
    "message_type": "job_vector",
    "id": "def456abc123",
    "source_url": "https://topcv.vn/...",
    "source_platform": "TopCV",
    "embedding": [0.234, 0.567, ...],  // 768 dimensions
    "metadata": {
        "title": "Senior AI Engineer",
        "company_name": "FPT",
        "location": "Hà Nội",
        "salary": "25-40 triệu"
    }
}
```

**Key:** Job ID (MD5 hash)

## Topic Configuration

```go
// Default topic settings
partitions: 3
replicationFactor: 1
config:
    retention.ms: 604800000  // 7 days
    compression.type: lz4
    max.message.bytes: 10485760  // 10MB
```

## Consumer Groups

| Consumer Group | Subscribed Topics | Service |
|----------------|-------------------|---------|
| `entity-extractor` | raw_articles, raw_jobs | Entity Extractor (Go) |
| `embedding-service-articles` | extracted_articles | Embedding Service (Python) |
| `embedding-service-jobs` | extracted_jobs | Embedding Service (Python) |
| `neo4j-writer` | extracted_articles, extracted_jobs | Neo4j Writer (Go) |
| `qdrant-writer` | article_vectors, job_vectors | Qdrant Writer (Go) |

## Data Flow Diagram

```
                    ┌─────────────────────────────────────────┐
                    │              CRAWLERS                    │
                    │   (VNExpress, GenK, DanTri, TopCV)       │
                    └────────────────┬────────────────────────┘
                                     │
                                     ▼
              ┌──────────────────────────────────────────────────┐
              │                  raw_articles                    │
              │                  raw_jobs                        │
              └────────────────────────┬─────────────────────────┘
                                       │
                                       ▼
                    ┌─────────────────────────────────────────┐
                    │           ENTITY EXTRACTOR               │
                    │              (Golang)                    │
                    └────────────────┬────────────────────────┘
                                     │
                                     ▼
              ┌──────────────────────────────────────────────────┐
              │              extracted_articles                  │
              │              extracted_jobs                      │
              └────────┬───────────────────────┬─────────────────┘
                       │                       │
                       ▼                       ▼
        ┌──────────────────────────┐   ┌──────────────────────────┐
        │    EMBEDDING SERVICE     │   │     NEO4J WRITER         │
        │        (Python)          │   │        (Golang)          │
        └────────────┬─────────────┘   └──────────────────────────┘
                     │
                     ▼
              ┌──────────────────────────────────────────────────┐
              │              article_vectors                     │
              │              job_vectors                         │
              └────────────────────────┬─────────────────────────┘
                                       │
                                       ▼
                    ┌─────────────────────────────────────────┐
                    │           QDRANT WRITER                  │
                    │              (Golang)                    │
                    └─────────────────────────────────────────┘
```

## Connection Configuration

### Producer Config

```python
# Python (kafka-python)
producer = KafkaProducer(
    bootstrap_servers="kafka:29092",
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks=1,
    retries=3,
    retry_backoff_ms=1000
)
```

### Consumer Config

```go
// Go (kafka-go)
reader := kafka.NewReader(kafka.ReaderConfig{
    Brokers:           []string{"kafka:29092"},
    Topic:             "raw_articles",
    GroupID:           "entity-extractor",
    MinBytes:          1,
    MaxBytes:          10e6,
    AutoCommit:        true,
})
```

## Monitoring

- **Kafka UI:** Accessible via Kafka Manager or Control Center
- **Metrics:** Messages/sec, consumer lag, partition status
- **Logs:** Consumer/producer errors, offset commits

## Hình Ảnh Minh Họa

> **Ghi chú:** Thêm ảnh Kafka topic overview tại đây
> 
> ![Kafka Topics](./images/kafka_topics.png)
> *Hình 1: Tổng quan các Kafka topics và data flow*

> **Ghi chú:** Thêm ảnh consumer groups diagram tại đây
> 
> ![Consumer Groups](./images/consumer_groups.png)
> *Hình 2: Sơ đồ consumer groups và subscriptions*