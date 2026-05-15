# Kiến Trúc Hệ Thống Database Module

## Tổng Quan Kiến Trúc

Database Module được thiết kế theo kiến trúc **microservices** với **event-driven** pattern, sử dụng **Apache Kafka** làm message broker để đảm bảo tính mở rộng và độ tin cậy.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           TECHPULSE VN - DATABASE MODULE                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│  │ VNExpress   │    │   GenK      │    │  DanTri     │    │   TopCV     │       │
│  │  Crawler    │    │  Crawler    │    │  Crawler    │    │  Crawler    │       │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘       │
│         │                  │                  │                  │              │
│         └──────────────────┼──────────────────┼──────────────────┘              │
│                            ▼                  ▼                                 │
│                    ┌───────────────────────────────┐                             │
│                    │      APACHE KAFKA             │                             │
│                    │   (Message Broker)            │                             │
│                    │                               │                             │
│                    │  Topics:                      │                             │
│                    │  • raw_articles               │                             │
│                    │  • raw_jobs                   │                             │
│                    │  • extracted_articles         │                             │
│                    │  • extracted_jobs             │                             │
│                    │  • article_vectors            │                             │
│                    │  • job_vectors                │                             │
│                    └───────────────┬───────────────┘                             │
│                                    │                                             │
│            ┌───────────────────────┼───────────────────────┐                    │
│            ▼                       ▼                       ▼                    │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │ Entity Extractor│    │ Embedding       │    │ Neo4j Writer    │             │
│  │ (Python)        │    │ Service         │    │ (Golang)        │             │
│  │                 │    │ (Python)        │    │                 │             │
│  │ PhoBERT/ELECTRA │    │ Sentence        │    │ Graph Storage   │             │
│  │ + Rule-based    │    │ Transformers    │    │                 │             │
│  │                 │    │ Transformers    │    │                 │             │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘             │
│           │                      │                      │                       │
│           ▼                      ▼                      ▼                       │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │ Extracted Data  │    │ Vector          │    │ NEO4J           │             │
│  │ (Kafka Topic)   │    │ Embeddings      │    │ Graph Database  │             │
│  └─────────────────┘    └────────┬────────┘    └─────────────────┘             │
│                                  │                                              │
│                                  ▼                                              │
│                         ┌─────────────────┐                                     │
│                         │ Qdrant Writer   │                                     │
│                         │ (Golang)        │                                     │
│                         └────────┬────────┘                                     │
│                                  │                                              │
│                                  ▼                                              │
│                         ┌─────────────────┐                                     │
│                         │ QDRANT          │                                     │
│                         │ Vector Database │                                     │
│                         └─────────────────┘                                     │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    APACHE AIRFLOW (Orchestrator)                         │   │
│  │                                                                          │   │
│  │  • Schedule: 22:00 Việt Nam (15:00 UTC) hàng ngày                        │   │
│  │  • Timeout: 2 giờ cho toàn bộ pipeline                                   │   │
│  │  • DAG: techpulse_daily_pipeline                                         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Thành phần | Công nghệ | Vai trò |
|------------|-----------|---------|
| **Orchestrator** | Apache Airflow 2.8.0 | Điều phối và lập lịch các task |
| **Message Broker** | Apache Kafka 7.5.0 | Xử lý luồng dữ liệu thời gian thực |
| **Coordination** | Apache Zookeeper | Quản lý Kafka cluster |
| **Graph Database** | Neo4j Aura (Cloud) | Lưu trữ dữ liệu dạng đồ thị |
| **Vector Database** | Qdrant Cloud (Disabled) | ~~Lưu trữ vector embeddings~~ |
| **NLP Engine** | PhoBERT/ELECTRA (Python) | Trích xuất thực thể |
| **Embedding Model** | SentenceTransformers (Disabled) | ~~Tạo vector embeddings~~ |
| **Containerization** | Docker + Docker Compose | Đóng gói và triển khai |

## Luồng Dữ Liệu Chi Tiết

### Bước 1: Thu Thập Dữ Liệu (Ingestion)

```
┌──────────────────────────────────────────────────────────────────┐
│                    AIRFLOW DAG TRIGGER                            │
│                    (22:00 VN Time Daily)                          │
└───────────────────────────┬──────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  VNExpress    │   │    GenK       │   │   DanTri      │
│   Crawler     │   │   Crawler     │   │   Crawler     │
│               │   │               │   │               │
│ Python +      │   │ Python +      │   │ Python +      │
│ Selenium      │   │ Selenium      │   │ Selenium      │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
              ┌─────────────────────────────┐
              │      RAW DATA OUTPUT        │
              │                             │
              │  1. Kafka Topic:            │
              │     • raw_articles          │
              │     • raw_jobs              │
              │                             │
              │  2. Local Storage:          │
              │     data/raw/{source}/      │
              │     DD_MM_YYYY.json         │
              └─────────────────────────────┘
```

### Bước 2: Xử Lý Dữ Liệu (Processing)

```
┌──────────────────────────────────────────────────────────────────┐
│                    KAFKA CONSUMER GROUPS                          │
└───────────────────────────┬──────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│    Entity     │   │   Embedding   │   │    Neo4j      │
│   Extractor   │   │   Service     │   │    Writer     │
│   (Python)    │   │   (Python)    │   │   (Golang)    │
│               │   │               │   │               │
│ Model:        │   │ Model:        │   │ Write:        │
│ ELECTRA NER   │   │ multilingual- │   │ • Articles    │
│ + Rule-based: │   │ e5-base       │   │ • Jobs        │
│ • TECH/DATE   │   │               │   │ • Companies   │
│ • JOB_ROLE    │   │ Dimension:    │   │ • Skills      │
│ • SALARY      │   │ 768           │   │ • Relations   │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Kafka Topic:  │   │ Kafka Topic:  │   │    NEO4J      │
│ extracted_    │   │ article_      │   │   DATABASE    │
│ articles      │   │ vectors       │   │               │
│ extracted_jobs│   │ job_vectors   │   │ Graph Schema  │
└───────────────┘   └───────┬───────┘   └───────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    Qdrant     │
                    │    Writer     │
                    │   (Golang)    │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    QDRANT     │
                    │   VECTOR DB   │
                    └───────────────┘
```

## Docker Services

```yaml
# Infrastructure Services
- airflow-webserver    # Airflow Web UI (port 8080)
- airflow-scheduler    # Airflow Scheduler
- zookeeper           # Kafka coordination
- kafka               # Message broker (ports 9094, 29092)

# Crawler Services
- crawler-vnexpress   # VNExpress crawler
- crawler-genk        # GenK crawler
- crawler-dantri      # DanTri crawler

# Processing Services
- embedding-service   # Python embedding service
- orchestrator        # Golang orchestrator (Entity Extractor + Neo4j Writer + Qdrant Writer)
```

## Network Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    techpulse-network                         │
│                    (Bridge Network)                          │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Airflow  │  │  Kafka   │  │ Crawlers │  │ Services │    │
│  │          │  │          │  │          │  │          │    │
│  │ :8080    │  │ :9094    │  │          │  │          │    │
│  │          │  │ :29092   │  │          │  │          │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│                                                              │
│  Volumes:                                                    │
│  • zookeeper-data    - Zookeeper persistence                │
│  • zookeeper-logs    - Zookeeper logs                       │
│  • kafka-data        - Kafka messages                       │
│  • airflow-data      - Airflow DB and logs                  │
└─────────────────────────────────────────────────────────────┘
```

## Hình Ảnh Minh Họa

> **Ghi chú:** Thêm ảnh kiến trúc tổng quan tại đây
> 
> ![Architecture Overview](./images/architecture_overview.png)
> *Hình 1: Kiến trúc tổng quan hệ thống TechPulse VN Database Module*

> **Ghi chú:** Thêm ảnh sơ đồ luồng dữ liệu tại đây
> 
> ![Data Flow](./images/data_flow.png)
> *Hình 2: Sơ đồ luồng dữ liệu từ crawler đến database*