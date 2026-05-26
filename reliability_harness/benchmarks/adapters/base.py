"""
Abstract base class for benchmark adapters.

An adapter is responsible for:
  1. Loading raw tasks from a source (local file, HuggingFace datasets, etc.).
  2. Normalising each raw task into the canonical BenchmarkTask schema.

Contracts:
  - Adapters must NOT download data on import.
  - Adapters must NOT call LLMs, Docker, or the sandbox.
  - Data loading happens only when load_tasks() is explicitly called.
  - normalize() must be a pure transformation — no I/O, no network.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from reliability_harness.benchmarks.task_schema import BenchmarkTask


class BenchmarkAdapter(ABC):
    """Abstract base for all ReliabilityHarness benchmark adapters."""

    #: Short lowercase identifier, e.g. "mbpp" or "humaneval".
    name: str

    @abstractmethod
    def load_tasks(
        self,
        split: str = "test",
        limit: int | None = None,
    ) -> list[BenchmarkTask]:
        """Load and return normalised benchmark tasks.

        Parameters
        ----------
        split:
            Dataset split to load ("test", "validation", "train").
            Benchmarks that have only one split should accept "test" and ignore
            this parameter.
        limit:
            If set, return at most this many tasks. Useful for smoke tests and
            dry-run validation.

        Returns
        -------
        list[BenchmarkTask]
            Tasks in the canonical schema, ready for the runtime layer.
        """
        ...

    @abstractmethod
    def normalize(self, raw_task: Any) -> BenchmarkTask:
        """Normalise a single raw task into the BenchmarkTask schema.

        Parameters
        ----------
        raw_task:
            A raw record as returned by the upstream dataset (dict, object, etc.).

        Returns
        -------
        BenchmarkTask
            The normalised task.
        """
        ...
