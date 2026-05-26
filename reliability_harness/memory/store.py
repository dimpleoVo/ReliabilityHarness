import json
import os
from typing import List
from reliability_harness.memory.schema import FailureMemoryItem
from reliability_harness.utils.paths import FAILURE_MEMORY_PATH

_DEFAULT_FAILURE_MEMORY_PATH: str = str(FAILURE_MEMORY_PATH)


class FailureMemoryStore:
    def __init__(self, path: str = _DEFAULT_FAILURE_MEMORY_PATH):
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def append(self, item: FailureMemoryItem):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")

    def load_all(self) -> List[dict]:
        if not os.path.exists(self.path):
            return []

        rows = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
        return rows