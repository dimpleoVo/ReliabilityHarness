"""
MBPP benchmark adapter skeleton.

MBPP (Mostly Basic Python Problems) — Austin et al., 2021.
  Paper: https://arxiv.org/abs/2108.07732
  Dataset: 374 / 500 tasks (sanitized / full splits).

Status: SKELETON — load_tasks() and normalize() raise NotImplementedError.
Full implementation will be added when MBPP integration is formally scoped.
"""
from __future__ import annotations

from typing import Any

from reliability_harness.benchmarks.adapters.base import BenchmarkAdapter
from reliability_harness.benchmarks.task_schema import BenchmarkTask


class MBPPAdapter(BenchmarkAdapter):
    """Adapter skeleton for the MBPP benchmark."""

    name = "mbpp"

    def load_tasks(
        self,
        split: str = "test",
        limit: int | None = None,
    ) -> list[BenchmarkTask]:
        """
        TODO (next benchmark phase): Load MBPP tasks.

        Expected data source: data/tasks/mbpp/ or HuggingFace `google-research-datasets/mbpp`.
        Expected splits: "test" (374 sanitized tasks), "train", "validation".

        Raises NotImplementedError until full integration is implemented.
        Use --dry-run in run_benchmark to validate the pipeline skeleton without
        loading data.
        """
        raise NotImplementedError(
            "MBPPAdapter.load_tasks() is not yet implemented. "
            "Full MBPP data loading will be added in the next benchmark phase. "
            "Run with --dry-run to inspect the pipeline skeleton."
        )

    def normalize(self, raw_task: Any) -> BenchmarkTask:
        """
        TODO (next benchmark phase): Map raw MBPP record to BenchmarkTask.

        Expected MBPP record fields:
          - task_id (int)       → task_id = f"mbpp_{raw_task['task_id']}"
          - text (str)          → prompt
          - code (str)          → reference_solution
          - test_list (list)    → tests
          - test_setup_code (str, optional) → metadata["test_setup_code"]

        Normalisation notes:
          - entry_point is None (MBPP does not specify a named entry point).
          - benchmark = "mbpp".
          - metadata includes source task_id int for traceability.
        """
        raise NotImplementedError(
            "MBPPAdapter.normalize() is not yet implemented."
        )
