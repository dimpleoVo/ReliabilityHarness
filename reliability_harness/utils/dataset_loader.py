import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from reliability_harness.utils.paths import DATA_ROOT, TASKS_ROOT

# Canonical task file name
_TASKS_FILE = "reliability_tasks.json"


def _resolve_dataset_path() -> Path:
    candidates = []

    # 1. RELIABILITY_HARNESS_DATASET_PATH — primary env override
    env = os.environ.get("RELIABILITY_HARNESS_DATASET_PATH")
    if env:
        candidates.append(Path(env))

    # 2. DATASET_PATH — secondary env override
    env = os.environ.get("DATASET_PATH")
    if env:
        candidates.append(Path(env))

    # 3. REACTX_DATASET_PATH — deprecated explicit alias; only used when explicitly set by user
    env = os.environ.get("REACTX_DATASET_PATH")
    if env:
        candidates.append(Path(env))

    # 4–5. Canonical data/ paths
    candidates.append(DATA_ROOT / _TASKS_FILE)
    candidates.append(TASKS_ROOT / _TASKS_FILE)

    for p in candidates:
        if p.exists():
            return p

    tried = [str(p) for p in candidates]
    raise FileNotFoundError(
        "Dataset not found. Tried:\n"
        + "\n".join(f"  {p}" for p in tried)
        + "\n\nTo fix, either:\n"
        + "  - Set RELIABILITY_HARNESS_DATASET_PATH=/path/to/reliability_tasks.json\n"
        + "  - Set DATASET_PATH=/path/to/reliability_tasks.json\n"
        + "  - Place tasks at data/tasks/reliability_tasks.json"
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
