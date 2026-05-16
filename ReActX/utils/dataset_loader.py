import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

_DATASET_FILENAME = "data/tasks/reactx_closed_loop_tasks.json"
_DOCKER_PATH = Path("/app/ReActX") / _DATASET_FILENAME
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _resolve_dataset_path() -> Path:
    candidates = []

    env = os.environ.get("REACTX_DATASET_PATH")
    if env:
        candidates.append(Path(env))

    candidates.append(_PROJECT_ROOT / _DATASET_FILENAME)
    candidates.append(_DOCKER_PATH)

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