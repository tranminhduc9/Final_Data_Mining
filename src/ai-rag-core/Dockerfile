FROM python:3.11-slim

WORKDIR /app

# Cài system deps cần cho torch và asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Cài Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Download models lúc build (tránh download lại mỗi lần start)
RUN python -c "\
from sentence_transformers import SentenceTransformer, CrossEncoder; \
from transformers import AutoTokenizer, AutoModelForTokenClassification; \
SentenceTransformer('intfloat/multilingual-e5-base'); \
CrossEncoder('BAAI/bge-reranker-v2-m3'); \
AutoTokenizer.from_pretrained('NlpHust/ner-vietnamese-electra-base'); \
AutoModelForTokenClassification.from_pretrained('NlpHust/ner-vietnamese-electra-base')"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
