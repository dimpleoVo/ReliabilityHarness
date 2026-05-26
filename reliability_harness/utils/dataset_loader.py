import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from reliability_harness.utils.paths import LEGACY_REACTX_ROOT

_DATASET_FILENAME = "data/tasks/reactx_closed_loop_tasks.json"
# temporary legacy data path — container mounts repo at /app, data still lives under ReActX/;
# to be updated when data/ is moved to repo root in Migration-2
_LEGACY_DOCKER_DATA_PATH = Path("/app/ReActX") / _DATASET_FILENAME
# legacy local path — points into ReActX/ subdir until data/ is migrated in Migration-2
_LEGACY_REACTX_DATA_ROOT = LEGACY_REACTX_ROOT


def _resolve_dataset_path() -> Path:
    candidates = []

    env = os.environ.get("REACTX_DATASET_PATH")
    if env:
        candidates.append(Path(env))

    candidates.append(_LEGACY_REACTX_DATA_ROOT / _DATASET_FILENAME)
    candidates.append(_LEGACY_DOCKER_DATA_PATH)

    for p in candidates:
        if p.exists():
            return p

    tried = [str(p) for p in candidates]
    raise FileNotFoundError(
        f"Dataset not found. Tried:\n" + "\n".join(f"  {p}" for p in tried)
    )


def load_dataset() -> List[Dict[str, Any]]:
    dataset_path = _resolve_dataset_path()

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Dataset file must be a JSON list.")

    return data


def normalize_text(text: str) -> str:
    return (text or "").strip().lower()


def get_ground_truth(task: str) -> Optional[str]:
    dataset = load_dataset()
    task_norm = normalize_text(task)

    # 1. exact match
    for item in dataset:
        candidate = normalize_text(item.get("task", ""))
        if task_norm == candidate:
            return item.get("gt")

    # 2. soft match
    for item in dataset:
        candidate = normalize_text(item.get("task", ""))
        if task_norm in candidate or candidate in task_norm:
            return item.get("gt")

    return None