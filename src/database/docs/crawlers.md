# Hệ Thống Crawler

## Tổng Quan

Hệ thống Crawler chịu trách nhiệm thu thập dữ liệu tin tức công nghệ và việc làm từ các nguồn khác nhau. Được viết bằng **Python** với sự hỗ trợ của **Selenium** cho các trang web động.

## Cấu Trúc Folder

```
crawl/
├── base_crawler.py      # Lớp cơ sở cho tất cả crawler
├── kafka_producer.py    # Tiện ích gửi dữ liệu đến Kafka
├── VNExpress.py         # Crawler cho VNExpress
├── GenK.py              # Crawler cho GenK
├── DanTri.py            # Crawler cho Dân Trí
├── TopCV.py             # Crawler cho TopCV (việc làm)
├── Dockerfile           # Docker image cho crawler
└── requirements.txt     # Python dependencies
```

## Base Crawler

### Chức Năng Chính

`BaseCrawler` là lớp trừu tượng cung cấp các chức năng chung cho tất cả crawler:

| Phương thức | Mô tả |
|-------------|-------|
| `setup()` | Khởi tạo thư mục, kết nối Kafka |
| `crawl()` | Phương thức trừu tượng - được implement bởi subclass |
| `run()` | Chạy crawler với error handling |
| `send_to_kafka_article()` | Gửi article đến Kafka topic |
| `send_to_kafka_job()` | Gửi job đến Kafka topic |
| `save_to_csv()` | Lưu dữ liệu dự phòng vào CSV |
| `cleanup()` | Đóng kết nối, giải phóng tài nguyên |

### Cấu Hình

```python
class BaseCrawler(ABC):
    MAX_ARTICLES = 150  # Số bài viết tối đa mỗi lần crawl
    
    def __init__(self, source_platform: str):
        self.source_platform = source_platform
        self.kafka_producer = CrawlerKafkaProducer()
        self.output_dir = "data/raw/{source_platform}/"
        self.kafka_enabled = False
```

## Kafka Producer

### Chức Năng

`CrawlerKafkaProducer` quản lý việc gửi dữ liệu đã crawl đến Kafka:

```python
class CrawlerKafkaProducer:
    def __init__(self):
        self.bootstrap_servers = "localhost:9094"
        self.topic_articles = "raw_articles"
        self.topic_jobs = "raw_jobs"
```

### Message Format

#### Article Message

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

#### Job Message

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
        "skills": ["Python", "TensorFlow", "PyTorch"],
        "source_url": "https://topcv.vn/...",
        "posted_date": "2026-05-14"
    }
}
```

## Các Crawler Cụ Thể

### 1. VNExpress Crawler

**Nguồn:** https://vnexpress.net/cong-ngoe

**Danh mục thu thập:**
- Sức khỏe công nghệ
- Công nghệ mới
- Điện máy
- Ô tô xe máy
- Science

**Đặc điểm:**
- Sử dụng Selenium để render JavaScript
- Trích xuất title, content, publish_date, author
- Lưu metadata URLs để tracking

### 2. GenK Crawler

**Nguồn:** https://genk.vn

**Danh mục thu thập:**
- Tin tức công nghệ
- Điện thoại
- Máy tính
- Công nghệ mới
- Khoa học

**Đặc điểm:**
- Parse HTML structure đặc thù GenK
- Xử lý phân trang tự động
- Extract related articles

### 3. DanTri Crawler

**Nguồn:** https://dantri.com.vn/cong-nghe

**Danh mục thu thập:**
- Tin tức công nghệ
- Điện thoại
- Máy tính
- Internet

**Đặc điểm:**
- Support both article và video content
- Handle dynamic content loading
- Extract image captions

### 4. TopCV Crawler (Jobs)

**Nguồn:** https://topcv.vn

**Loại dữ liệu:**
- Job listings
- Company information
- Salary ranges
- Required skills

**Đặc điểm:**
- Crawl job listings từ multiple pages
- Extract structured job data
- Handle company profiles

## Sơ Đồ Hoạt Động

```
┌─────────────────────────────────────────────────────────────┐
│                    CRAWLER WORKFLOW                          │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────────┐
              │     1. KHỞI TẠO (setup)     │
              │  • Tạo thư mục data/raw     │
              │  • Kết nối Kafka            │
              │  • Khởi tạo CSV file        │
              └─────────────┬───────────────┘
                            │
                            ▼
              ┌─────────────────────────────┐
              │     2. CRAWL (crawl)        │
              │  • Request đến target URL   │
              │  • Parse HTML/JS            │
              │  • Extract data             │
              └─────────────┬───────────────┘
                            │
                            ▼
              ┌─────────────────────────────┐
              │     3. XỬ LÝ DỮ LIỆU        │
              │  • Clean text               │
              │  • Normalize format         │
              │  • Validate required fields │
              └─────────────┬───────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
    ┌──────────────────┐       ┌──────────────────┐
    │  4a. SEND KAFKA  │       │  4b. SAVE LOCAL  │
    │  • raw_articles  │       │  • DD_MM_YYYY.   │
    │  • raw_jobs      │       │    json          │
    └──────────────────┘       │  • URLs metadata │
                               └──────────────────┘
                            │
                            ▼
              ┌─────────────────────────────┐
              │     5. CLEANUP (cleanup)    │
              │  • Close Kafka producer     │
              │  • Log statistics           │
              └─────────────────────────────┘
```

## Cấu Hình Docker

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Selenium dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Copy crawler code
COPY . .

CMD ["python", "VNExpress.py"]
```

### Environment Variables

| Biến | Mô tả | Mặc định |
|------|-------|----------|
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker addresses | `localhost:9094` |
| `MAX_ARTICLES` | Số bài tối đa/crawl | `150` |
| `CRAWL_TIMEOUT_HOURS` | Timeout cho crawl | `2` |

## Lịch Trình Airflow

Crawlers được điều phối bởi Airflow DAG `techpulse_daily_pipeline`:

```python
# Schedule: 22:00 Việt Nam (15:00 UTC) hàng ngày

[scrape_vnexpress, scrape_genk, scrape_dantri] >> run_processing
```

**Timeout:** 2 giờ cho mỗi crawler

## Data Storage

### Cấu trúc thư mục

```
data/
├── raw/                          # Dữ liệu thô
│   ├── vnexpress/
│   │   ├── 14_05_2026.json       # Articles crawl ngày 14/05
│   │   ├── 14_05_2026_urls.txt   # URLs đã crawl
│   │   └── metadata/
│   │       └── 14_05_2026_urls.txt
│   ├── genk/
│   │   └── ...
│   ├── dantri/
│   │   └── ...
│   └── topcv/
│       └── ...
└── processed/                    # Dữ liệu đã xử lý
    └── sample.json
```

### JSON Format

```json
[
    {
        "title": "OpenAI ra mắt GPT-5 với khả năng reasoning vượt trội",
        "content": "Nội dung đầy đủ bài viết...",
        "publish_date": "14/05/2026",
        "source_url": "https://vnexpress.net/openai-ra-mat-gpt-5-123456.html",
        "author": "Nguyễn Văn A",
        "category": "Công nghệ"
    }
]
```

## Error Handling

| Exception | Xử lý |
|-----------|-------|
| `ConnectionError` | Retry 3 lần, skip nếu fail |
| `TimeoutException` | Log warning, continue |
| `NoSuchElementException` | Skip element, continue |
| `KafkaError` | Fallback to local CSV |

## Monitoring

- **Logs:** stdout với log level INFO
- **Metrics:** Article count, error count, duration
- **Health Check:** Docker container status

## Hình Ảnh Minh Họa

> **Ghi chú:** Thêm ảnh sơ đồ crawler workflow tại đây
> 
> ![Crawler Workflow](./images/crawler_workflow.png)
> *Hình 1: Sơ đồ hoạt động của hệ thống crawler*

> **Ghi chú:** Thêm ảnh kiến trúc Kafka producer tại đây
> 
> ![Kafka Producer](./images/kafka_producer.png)
> *Hình 2: Kiến trúc Kafka producer trong crawler*