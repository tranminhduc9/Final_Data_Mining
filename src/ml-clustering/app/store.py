"""
AppStore — load và cache artifacts từ disk khi startup.

Artifacts:
  - best_labels.parquet  : tech_id → cluster_id
  - cluster_labels.json  : cluster_id → label metadata
  - technologies.parquet : tech_id → name (từ snapshot)

Dùng singleton pattern: gọi `get_store()` ở bất kỳ đâu.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
import pandas as pd

from conf.config import DATA_DIR, load_params


def _get_s3_settings() -> dict | None:
    bucket = os.getenv("MLCLUSTER_S3_BUCKET")
    if not bucket:
        return None

    prefix = os.getenv("MLCLUSTER_S3_PREFIX", "").strip("/")
    cache_dir = os.getenv("MLCLUSTER_S3_CACHE_DIR", "")
    endpoint_url = os.getenv("MLCLUSTER_S3_ENDPOINT_URL")
    region = os.getenv("MLCLUSTER_S3_REGION")
    access_key = os.getenv("MLCLUSTER_S3_ACCESS_KEY_ID")
    secret_key = os.getenv("MLCLUSTER_S3_SECRET_ACCESS_KEY")
    addressing_style = os.getenv("MLCLUSTER_S3_ADDRESSING_STYLE")

    return {
        "bucket": bucket,
        "prefix": prefix,
        "cache_dir": cache_dir,
        "endpoint_url": endpoint_url,
        "region": region,
        "access_key": access_key,
        "secret_key": secret_key,
        "addressing_style": addressing_style,
    }


def _make_s3_client(settings: dict) -> boto3.client:
    config = None
    if settings.get("addressing_style"):
        config = Config(s3={"addressing_style": settings["addressing_style"]})

    return boto3.client(
        "s3",
        endpoint_url=settings.get("endpoint_url") or None,
        region_name=settings.get("region") or None,
        aws_access_key_id=settings.get("access_key") or None,
        aws_secret_access_key=settings.get("secret_key") or None,
        config=config,
    )


def _s3_key(prefix: str, rel_path: str) -> str:
    if prefix:
        return f"{prefix}/{rel_path}"
    return rel_path


def _local_path(cache_dir: str, rel_path: str) -> Path:
    base = Path(cache_dir) if cache_dir else DATA_DIR
    return base / rel_path


def _ensure_s3_file(settings: dict, rel_path: str) -> Path:
    local_path = _local_path(settings.get("cache_dir", ""), rel_path)
    if local_path.exists():
        return local_path

    local_path.parent.mkdir(parents=True, exist_ok=True)
    key = _s3_key(settings.get("prefix", ""), rel_path)
    client = _make_s3_client(settings)
    try:
        client.download_file(settings["bucket"], key, str(local_path))
    except (BotoCoreError, ClientError) as exc:
        raise FileNotFoundError(f"S3 download failed: s3://{settings['bucket']}/{key}") from exc
    return local_path


class AppStore:
    """
    Chứa toàn bộ dữ liệu phục vụ API.
    Được load 1 lần khi app khởi động.
    """

    def __init__(self) -> None:
        params = load_params()
        self.tag: str = params.snapshot.tag

        s3_settings = _get_s3_settings()

        labels_rel = f"models/{self.tag}/best_labels.parquet"
        cluster_labels_rel = f"labels/{self.tag}/cluster_labels.json"
        tech_rel = f"raw/snapshot_{self.tag}/technologies.parquet"

        # --- best_labels: tech_id → cluster_id ---
        labels_path = (
            _ensure_s3_file(s3_settings, labels_rel)
            if s3_settings else DATA_DIR / labels_rel
        )
        df_labels = pd.read_parquet(labels_path)
        # cluster_id = -1 → noise
        self.labels_df: pd.DataFrame = df_labels  # cols: tech_id, cluster_id

        # --- cluster_labels: dict[str, dict] hoặc list[dict] ---
        labels_json = (
            _ensure_s3_file(s3_settings, cluster_labels_rel)
            if s3_settings else DATA_DIR / cluster_labels_rel
        )
        with open(labels_json, encoding="utf-8") as f:
            raw_labels = json.load(f)
        # Hỗ trợ cả 2 format: dict{"0": {...}} và list[{cluster_id: 0, ...}]
        if isinstance(raw_labels, dict):
            self.cluster_labels: dict[int, dict] = {
                int(k): v for k, v in raw_labels.items()
            }
        else:
            self.cluster_labels = {int(c["cluster_id"]): c for c in raw_labels}

        # --- technologies snapshot: tech_id → name ---
        tech_path = (
            _ensure_s3_file(s3_settings, tech_rel)
            if s3_settings else DATA_DIR / tech_rel
        )
        df_tech = pd.read_parquet(tech_path)
        # Tạo 2 index: tech_id→name và name_lower→tech_id (để lookup theo tên)
        self.id_to_name: dict[str, str] = dict(
            zip(df_tech["tech_id"], df_tech["name"])
        )
        self.name_lower_to_id: dict[str, str] = {
            n.lower(): tid for tid, n in self.id_to_name.items()
        }

        # --- Merge: tech_id → cluster_id (chỉ techs đã cluster, bỏ noise=-1) ---
        self.tech_to_cluster: dict[str, int] = {
            row["tech_id"]: int(row["cluster_id"])
            for _, row in df_labels.iterrows()
        }

        # --- Ngược lại: cluster_id → list tech names ---
        self.cluster_to_techs: dict[int, list[str]] = {}
        for tech_id, cid in self.tech_to_cluster.items():
            name = self.id_to_name.get(tech_id, tech_id)
            self.cluster_to_techs.setdefault(cid, []).append(name)

    def lookup_tech(self, name: str) -> tuple[str | None, int | None]:
        """
        Tìm (tech_id, cluster_id) theo tên (case-insensitive).
        Trả về (None, None) nếu không tìm thấy.
        """
        tech_id = self.name_lower_to_id.get(name.lower())
        if tech_id is None:
            return None, None
        cluster_id = self.tech_to_cluster.get(tech_id)
        return tech_id, cluster_id

    def get_cluster_label(self, cluster_id: int) -> dict | None:
        return self.cluster_labels.get(cluster_id)


@lru_cache(maxsize=1)
def get_store() -> AppStore:
    """Singleton — load 1 lần, cache suốt vòng đời app."""
    return AppStore()
