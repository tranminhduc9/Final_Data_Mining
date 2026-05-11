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
from functools import lru_cache
from pathlib import Path

import pandas as pd

from conf.config import DATA_DIR, load_params


class AppStore:
    """
    Chứa toàn bộ dữ liệu phục vụ API.
    Được load 1 lần khi app khởi động.
    """

    def __init__(self) -> None:
        params = load_params()
        self.tag: str = params.snapshot.tag

        # --- best_labels: tech_id → cluster_id ---
        labels_path = DATA_DIR / "models" / self.tag / "best_labels.parquet"
        df_labels = pd.read_parquet(labels_path)
        # cluster_id = -1 → noise
        self.labels_df: pd.DataFrame = df_labels  # cols: tech_id, cluster_id

        # --- cluster_labels: dict[str, dict] hoặc list[dict] ---
        labels_json = DATA_DIR / "labels" / self.tag / "cluster_labels.json"
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
        snap_dir = DATA_DIR / "raw" / f"snapshot_{self.tag}"
        tech_path = snap_dir / "technologies.parquet"
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
