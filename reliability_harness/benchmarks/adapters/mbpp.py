"""
MBPP benchmark adapter — small fixture implementation.

Benchmark-2: loads from data/fixtures/mbpp_small.json.
No LLM calls. No Docker. No network. No sandbox.
"""
from __future__ import annotations

import json
from typing import Any

from reliability_harness.benchmarks.adapters.base import BenchmarkAdapter
from reliability_harness.benchmarks.task_schema import BenchmarkTask
from reliability_harness.utils.paths import DATA_ROOT

_FIXTURE_PATH = DATA_ROOT / "fixtures" / "mbpp_small.json"


class MBPPAdapter(BenchmarkAdapter):
    """Adapter for MBPP (Mostly Basic Python Problems) — small fixture."""

    name = "mbpp"
    FIXTURE_PATH = _FIXTURE_PATH

    def load_tasks(
        self,
        split: str = "test",
        limit: int | None = None,
    ) -> list[BenchmarkTask]:
        """Load MBPP tasks from the local small fixture file.

        Parameters
        ----------
        split:
            Accepted for API compatibility; only "test" is present in the fixture.
        limit:
            If set, return at most this many tasks.
        """
        with open(self.FIXTURE_PATH, encoding="utf-8") as f:
            raw_tasks = json.load(f)

        tasks = [self.normalize(raw) for raw in raw_tasks]

        if limit is not None:
            tasks = tasks[:limit]

        return tasks

    def normalize(self, raw_task: Any) -> BenchmarkTask:
        """Map a raw fixture record to BenchmarkTask."""
        return BenchmarkTask(
            task_id=raw_task["task_id"],
            benchmark=raw_task["benchmark"],
            prompt=raw_task["prompt"],
            entry_point=raw_task.get("entry_point"),
            tests=raw_task.get("tests", []),
            reference_solution=raw_task.get("reference_solution"),
            metadata=raw_task.get("metadata", {}),
        )
