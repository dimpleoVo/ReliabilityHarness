"""
TinyFixtureAdapter — local deterministic fixture benchmark for pipeline smoke tests.

Reads from data/fixtures/tiny_code_tasks.json.
No LLM calls. No Docker. No network. No sandbox.
Safe to import and run at any time.
"""
from __future__ import annotations

import json
from typing import Any

from reliability_harness.benchmarks.adapters.base import BenchmarkAdapter
from reliability_harness.benchmarks.task_schema import BenchmarkTask
from reliability_harness.utils.paths import DATA_ROOT

_FIXTURE_PATH = DATA_ROOT / "fixtures" / "tiny_code_tasks.json"


class TinyFixtureAdapter(BenchmarkAdapter):
    """Adapter for the local tiny fixture benchmark.

    Loads tasks from data/fixtures/tiny_code_tasks.json.
    Intended for pipeline integration tests and dry-run smoke tests only.
    Not a real research benchmark.
    """

    name = "tiny"
    FIXTURE_PATH = _FIXTURE_PATH

    def load_tasks(
        self,
        split: str = "test",
        limit: int | None = None,
    ) -> list[BenchmarkTask]:
        with open(self.FIXTURE_PATH, encoding="utf-8") as f:
            raw_tasks = json.load(f)

        tasks = [self.normalize(raw) for raw in raw_tasks]

        if limit is not None:
            tasks = tasks[:limit]

        return tasks

    def normalize(self, raw_task: Any) -> BenchmarkTask:
        return BenchmarkTask(
            task_id=raw_task["task_id"],
            benchmark=raw_task["benchmark"],
            prompt=raw_task["prompt"],
            entry_point=raw_task.get("entry_point"),
            tests=raw_task.get("tests", []),
            reference_solution=raw_task.get("reference_solution"),
            metadata=raw_task.get("metadata", {}),
        )
