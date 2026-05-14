# ml-clustering — Hệ thống phân cụm Technology

Module độc lập trong dự án **TechPulse** — dùng Scikit-learn làm core, Neo4j GDS sinh feature từ đồ thị tri thức, DVC quản lý phiên bản dữ liệu, MLflow track tham số/chỉ số, Gemini 2.5 Flash tự động đặt tên cụm.

## 1. Mục tiêu

Phân cụm **1,137 node `:Technology`** đang nằm trong Neo4j AuraDB (đồ thị tri thức TechPulse) thành các nhóm có ý nghĩa (ví dụ: "AI/ML stack", "Frontend JS framework", "Cloud infra", "Mobile native"…) để:

1. Thay thế trường `category` hiện tại (97% là `"Other"` — vô giá trị).
2. Cấp dữ liệu cho Trend Analysis (gom xu hướng theo cụm thay vì từng tech rời rạc).
3. Hỗ trợ recommendation cho user roadmap (tech cùng cụm = học tiếp được).

## 2. Kết luận khảo sát thực tế (đã inspect AuraDB ngày 06/05/2026)

| Hạng mục | Giá trị |
|---|---|
| `Technology` nodes | 1,137 |
| Có degree ≥ 5 | 391 (34%) — "lõi" để cluster ổn định |
| Có degree ≤ 2 | 603 (53%) — DBSCAN sẽ tự đẩy vào nhóm noise |
| GDS plugin trên AuraDB | ✅ 393 procedures sẵn sàng |
| APOC plugin trên AuraDB | ✅ v2026.04.0 |
| Article embedding (768d) đã có | 526 / 834 bài |
| Cạnh `(Article)-[:MENTIONS]->(Technology)` | 15,957 |
| Cạnh `(Company)-[:USES]->(Technology)` | 11,296 |
| Cạnh `(Job)-[:REQUIRES]->(Technology)` | 4,916 |
| Cạnh `(Technology)-[:RELATED_TO]->(Technology)` | 70 |

**Hệ quả thiết kế:**
- DBSCAN/HDBSCAN ưu tiên hơn KMeans (vì có ~53% node "thưa" đáng coi là noise).
- Có thể chạy GDS thẳng trên AuraDB, không cần ETL về local.
- Content feature mạnh: lấy mean embedding 768d của các Article có MENTIONS từng tech (Bag-of-Articles).

## 3. Kiến trúc luồng xử lý

```
                    ┌─────────────────────────────┐
                    │    Neo4j AuraDB (cloud)     │
                    │  Technology / Article / ... │
                    └──────────────┬──────────────┘
                                   │
        ┌──────────────────────────┴──────────────────────────┐
        │                                                     │
        ▼                                                     ▼
  Stage 1: EXTRACT                                  Stage 2: FEATURES
  pipelines/stage_01_extract.py                     pipelines/stage_02_features.py
  data/raw/snapshot_<tag>/                          data/features/<tag>/X.npy
   ├ technologies.parquet                            + tech_ids.parquet
   ├ companies.parquet                               + feature_meta.json
   ├ articles.parquet                               (tracked by DVC)
   ├ jobs.parquet
   └ edges.parquet
  (tracked by DVC)
                                                     ┌────────────────────┐
                                                     │  GDS in-memory     │
                                                     │  (FastRP, PageRank,│
                                                     │   Louvain, degree) │
                                                     └────────────────────┘
                                                     │
                                                     ▼
                                              Stage 3: TRAIN
                                              pipelines/stage_03_train.py
                                              ├ DBSCAN/HDBSCAN/KMeans
                                              ├ Grid search eps/min_samples
                                              ├ Silhouette / DB / Calinski
                                              └ MLflow log + register best
                                                     │
                                                     ▼
                                              Stage 4: LABEL
                                              pipelines/stage_04_label.py
                                              Gemini 2.5 Flash gán tên cụm
                                              data/labels/<tag>/cluster_labels.json
                                                     │
                                                     ▼
                                              Stage 5: WRITEBACK (optional)
                                              pipelines/stage_05_writeback.py
                                              Ghi cluster_id, cluster_label
                                              ngược về Neo4j (APOC batch)
```

Mỗi stage là một **DVC stage** trong `dvc.yaml`, input/output rõ ràng, có thể `dvc repro` để tái lập toàn bộ pipeline.

## 4. Tech stack chốt

| Thành phần | Công nghệ |
|---|---|
| Core ML | Scikit-learn 1.5+ |
| Graph features | Neo4j GDS (FastRP, PageRank, Louvain, degreeCentrality) |
| Content features | Article embedding 768d sẵn có (multilingual-e5-base) |
| Versioning data | DVC 3.x (remote tuỳ chọn — local hoặc S3) |
| Experiment tracking | MLflow 2.x (sqlite backend cho dev, postgres khi prod) |
| Auto label | Gemini 2.5 Flash qua `langchain-google-genai` |
| Outlier-friendly clusterer | HDBSCAN (`hdbscan` package) |

## 5. Cấu trúc thư mục

```
src/ml-clustering/
├── README.md                               # tài liệu này
├── requirements.txt
├── dvc.yaml                                # định nghĩa 5 stage
├── params.yaml                             # eps, min_samples, model name…
├── conf/
│   └── config.py                           # load .env, paths, neo4j conn
├── data/                                   # gitignored, DVC-tracked
│   ├── raw/snapshot_<tag>/
│   ├── features/<tag>/
│   └── labels/<tag>/
├── src/
│   ├── data/{neo4j_loader,snapshot}.py
│   ├── features/{gds_features,content_features,graph_features,feature_pipeline}.py
│   ├── clustering/{trainer,tuner,evaluator}.py
│   ├── labeling/{llm_labeler.py, prompts/cluster_label.txt}
│   └── tracking/mlflow_logger.py
├── pipelines/
│   ├── stage_01_extract.py
│   ├── stage_02_features.py
│   ├── stage_03_train.py
│   ├── stage_04_label.py
│   └── stage_05_writeback.py
└── tests/
    ├── unit/
    └── integration/
```

## 6. Quy ước

- **Tham số ở `params.yaml`** — không hardcode trong code. Mọi thay đổi tham số phải đi qua DVC để re-run được.
- **Mọi run đều log MLflow** — với tag `dataset_snapshot=<tag>` để biết model nào ứng với snapshot data nào.
- **Không gọi Gemini trong vòng lặp huấn luyện** — chỉ gọi 1 lần ở Stage 4 với cụm đã chốt.
- **Tham số hoá Cypher** — không nối f-string, để cache execution plan.
- **`tech_id` chính = `elementId(t)` của Neo4j** — bền vững hơn `name` (có thể trùng lower-case sau cleaning).

## 7. Cách chạy

```bash
cd src/ml-clustering
pip install -r requirements.txt

# Chạy toàn bộ pipeline lần đầu
dvc repro

# Hoặc chạy từng stage
python -m pipelines.stage_01_extract --tag 2026-05-06
python -m pipelines.stage_02_features --tag 2026-05-06
python -m pipelines.stage_03_train --tag 2026-05-06 --experiment tech_clustering_v1
python -m pipelines.stage_04_label --run-id <mlflow_run_id>
python -m pipelines.stage_05_writeback --run-id <mlflow_run_id>   # optional

# Xem kết quả MLflow
mlflow ui --backend-store-uri sqlite:///mlruns.db
```

## 8. Trách nhiệm code (đề xuất)

- Stage 1–2 (data + features): 1 người, ~3 ngày.
- Stage 3 (train + tune + MLflow): 1 người, ~3 ngày.
- Stage 4 (Gemini label): 1 người, ~1 ngày.
- Stage 5 (writeback Neo4j) + tests + DVC wiring: 1 người, ~2 ngày.
