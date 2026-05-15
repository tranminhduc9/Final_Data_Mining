# Deployment Guide

## Tổng Quan

Hướng dẫn triển khai hệ thống Database Module sử dụng Docker Compose. Hệ thống được thiết kế để chạy trong môi trường containerized, đảm bảo tính nhất quán giữa development và production.

## Yêu Cầu Hệ Thống

### Minimum Requirements

| Yêu cầu | Giá trị |
|---------|---------|
| CPU | 4 cores |
| RAM | 8 GB |
| Disk | 50 GB |
| OS | Linux / macOS / Windows (WSL2) |

### Software Prerequisites

| Software | Version |
|----------|---------|
| Docker | 20.10+ |
| Docker Compose | 2.0+ |
| Git | 2.0+ |

### Ports Required

| Port | Service |
|------|---------|
| 8080 | Airflow Webserver |
| 9094 | Kafka (External) |
| 29092 | Kafka (Internal) |
| 2181 | Zookeeper |
| 7687 | Neo4j |
| 7474 | Neo4j Browser |
| 6333 | Qdrant |

## Cấu Trúc Docker Compose

```yaml
# docker-compose.yml structure
services:
  # Airflow Orchestration
  airflow-webserver:
    image: apache/airflow:2.8.0-python3.10
    ports: ["8080:8080"]
    
  airflow-scheduler:
    image: apache/airflow:2.8.0-python3.10
    
  # Infrastructure
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    ports: ["9094:9094", "29092:29092"]
    
  # Crawlers
  crawler-vnexpress:
    build: ./crawl
    
  crawler-genk:
    build: ./crawl
    
  crawler-dantri:
    build: ./crawl
    
  # Processing Services
  embedding-service:
    build: ./services/embedding_service
    
  orchestrator:
    build: .
```

## Biến Môi Trường

### File .env

Tạo file `.env` trong thư mục root project:

```bash
# ==================== AIRFLOW ====================
AIRFLOW_FERNET_KEY=your_fernet_key_here
AIRFLOW_DAGS_FOLDER=/opt/airflow/dags
AIRFLOW_WEBSERVER_HOST=0.0.0.0
AIRFLOW_WEBSERVER_PORT=8080
AIRFLOW_DAG_DIR_LIST_INTERVAL=30

# ==================== KAFKA ====================
KAFKA_BOOTSTRAP_SERVERS=kafka:29092

# ==================== NEO4J AURA (CLOUD) ====================
# Neo4j Aura connection - get from Neo4j Aura console
# Format: neo4j+s://xxx.databases.neo4j.io
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_aura_password_here
NEO4J_DATABASE=neo4j

# ==================== QDRANT CLOUD (FREE) ====================
# Qdrant Cloud - get from https://cloud.qdrant.io
QDRANT_URL=https://your-cluster-url.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key_here
QDRANT_COLLECTION_ARTICLES=articles
QDRANT_COLLECTION_JOBS=jobs

# ==================== CRAWLER ====================
MAX_ARTICLES=150
CRAWL_TIMEOUT_HOURS=2
```

### Cloud Services Setup

#### Neo4j Aura Setup

1. Đăng ký tại https://neo4j.com/cloud/aura/
2. Tạo instance mới (Free tier available)
3. Lấy connection details từ console:
   - URI: `neo4j+s://xxx.databases.neo4j.io`
   - Username: `neo4j`
   - Password: (được cung cấp khi tạo)

#### Qdrant Cloud Setup

1. Đăng ký tại https://cloud.qdrant.io/
2. Tạo cluster mới (Free tier: 1GB storage)
3. Lấy connection details:
   - URL: `https://xxx.qdrant.io`
   - API Key: tạo trong dashboard

### Fernet Key Generation

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Khởi Động Hệ Thống

### 1. Clone Repository

```bash
git clone https://github.com/your-repo/Final_Data_Mining.git
cd Final_Data_Mining/src/database
```

### 2. Tạo .env File

```bash
cp ../../.env.example ../../.env
# Edit .env with your configurations
```

### 3. Build Images

```bash
docker-compose build
```

### 4. Khởi Động Services

```bash
# Start all services
docker-compose up -d

# Or start specific services
docker-compose up -d zookeeper kafka
docker-compose up -d airflow-webserver airflow-scheduler
docker-compose up -d crawler-vnexpress crawler-genk crawler-dantri
docker-compose up -d embedding-service orchestrator
```

### 5. Kiểm Tra Trạng Thái

```bash
# Check all containers
docker-compose ps

# Check logs
docker-compose logs -f [service_name]
```

## Thứ Tự Khởi Động

```
┌─────────────────────────────────────────────────────────────┐
│                    STARTUP ORDER                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Infrastructure (zookeeper, kafka)                       │
│     │                                                        │
│     ▼                                                        │
│  2. Airflow (airflow-webserver, airflow-scheduler)          │
│     │                                                        │
│     ▼                                                        │
│  3. Crawlers (crawler-*)                                     │
│     │                                                        │
│     ▼                                                        │
│  4. Processing Services (embedding-service, orchestrator)    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Kiểm Tra Health

### Airflow

```bash
# Check Airflow UI
open http://localhost:8080

# Default credentials
Username: airflow
Password: airflow
```

### Kafka

```bash
# List topics
docker exec kafka kafka-topics --list --bootstrap-server localhost:9094

# Consume messages
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9094 \
  --topic raw_articles \
  --from-beginning
```

### Neo4j

```bash
# Check Neo4j Browser
open http://localhost:7474

# Test connection
docker exec neo4j cypher-shell -u neo4j -p password "RETURN 1;"
```

## Dừng Hệ Thống

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop specific service
docker-compose stop [service_name]
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Kafka connection refused | Wait for Kafka to fully start (30-60s) |
| Airflow DAG not appearing | Check DAG folder path in .env |
| Neo4j connection failed | Verify NEO4J_PASSWORD is correct |
| Out of memory | Increase Docker memory limit |

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f kafka
docker-compose logs -f airflow-scheduler
docker-compose logs -f orchestrator
```

### Reset System

```bash
# Full reset
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

## Makefile Commands

```makefile
# Available commands
make build        # Build all images
make up           # Start all services
make down         # Stop all services
make logs         # View logs
make reset        # Full reset
make test         # Run tests
```

## Production Considerations

### 1. Security

- Thay đổi tất cả default passwords
- Sử dụng secrets management (Vault, AWS Secrets Manager)
- Enable TLS cho Kafka, Neo4j
- Configure firewall rules

### 2. Scalability

```yaml
# Scale crawlers
docker-compose up -d --scale crawler-vnexpress=3

# Increase Kafka partitions
docker exec kafka kafka-topics --alter \
  --topic raw_articles \
  --partitions 6 \
  --bootstrap-server localhost:9094
```

### 3. Monitoring

- Deploy Prometheus + Grafana
- Configure Kafka metrics
- Set up alerting rules
- Enable Neo4j monitoring

### 4. Backup

```bash
# Backup Neo4j
docker exec neo4j neo4j-admin database dump neo4j --to-path=/backup

# Backup Kafka topics
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9094 \
  --topic raw_articles \
  --from-beginning > backup_raw_articles.json
```

## Hình Ảnh Minh Họa

> **Ghi chú:** Thêm ảnh deployment diagram tại đây
> 
> ![Deployment Diagram](./images/deployment_diagram.png)
> *Hình 1: Sơ đồ triển khai hệ thống*

> **Ghi chú:** Thêm ảnh Docker architecture tại đây
> 
> ![Docker Architecture](./images/docker_architecture.png)
> *Hình 2: Kiến trúc Docker containers*