from typing import List, Dict


def simple_task_type(task: str) -> str:
    t = task.lower()
    if "print" in t or "python" in t or "code" in t:
        return "code"
    if "string" in t:
        return "string"
    if "list" in t:
        return "list"
    if "fibonacci" in t or "math" in t:
        return "math"
    return "general"


class FailureMemoryRetriever:
    def __init__(self, store):
        self.store = store

    def retrieve(self, task: str, top_k: int = 3) -> List[Dict]:
        all_rows = self.store.load_all()
        task_type = simple_task_type(task)

        scored = []
        for row in all_rows:
            score = 0

            if row.get("task_type") == task_type:
                score += 2

            if row.get("error_type") == "runtime_error":
                score += 1

            old_task = row.get("task", "").lower()
            for token in task.lower().split():
                if token and token in old_task:
                    score += 1

            if row.get("improved") is True:
                score += 2

            if score > 0:
                scored.append((score, row))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [row for _, row in scored[:top_k]]