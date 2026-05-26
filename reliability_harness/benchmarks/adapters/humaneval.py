"""
HumanEval benchmark adapter skeleton.

HumanEval — Chen et al., 2021 (Evaluating Large Language Models Trained on Code).
  Paper: https://arxiv.org/abs/2107.03374
  Dataset: 164 hand-written Python programming problems.

Status: SKELETON — load_tasks() and normalize() raise NotImplementedError.
Full implementation will be added when HumanEval integration is formally scoped.
"""
from __future__ import annotations

from typing import Any

from reliability_harness.benchmarks.adapters.base import BenchmarkAdapter
from reliability_harness.benchmarks.task_schema import BenchmarkTask


class HumanEvalAdapter(BenchmarkAdapter):
    """Adapter skeleton for the HumanEval benchmark."""

    name = "humaneval"

    def load_tasks(
        self,
        split: str = "test",
        limit: int | None = None,
    ) -> list[BenchmarkTask]:
        """
        TODO (next benchmark phase): Load HumanEval tasks.

        Expected data source: data/tasks/humaneval/ or HuggingFace `openai_humaneval`.
        HumanEval has a single split ("test", 164 tasks).

        Raises NotImplementedError until full integration is implemented.
        Use --dry-run in run_benchmark to validate the pipeline skeleton without
        loading data.
        """
        raise NotImplementedError(
            "HumanEvalAdapter.load_tasks() is not yet implemented. "
            "Full HumanEval data loading will be added in the next benchmark phase. "
            "Run with --dry-run to inspect the pipeline skeleton."
        )

    def normalize(self, raw_task: Any) -> BenchmarkTask:
        """
        TODO (next benchmark phase): Map raw HumanEval record to BenchmarkTask.

        Expected HumanEval record fields:
          - task_id (str)              → task_id (e.g. "HumanEval/0")
          - prompt (str)               → prompt
          - canonical_solution (str)   → reference_solution
          - test (str)                 → tests = [raw_task["test"]]
          - entry_point (str)          → entry_point

        Normalisation notes:
          - benchmark = "humaneval".
          - metadata = {} (no additional fields needed).
          - The test string is a self-contained Python module with check() calls.
        """
        raise NotImplementedError(
            "HumanEvalAdapter.normalize() is not yet implemented."
        )
