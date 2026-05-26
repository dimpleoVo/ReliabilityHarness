"""
Benchmark-normalized task schema for ReliabilityHarness paper experiments.

BenchmarkTask is the single contract between the adapter layer and the runtime
layer. All benchmark adapters (MBPP, HumanEval, future benchmarks) must produce
BenchmarkTask instances. The runtime layer consumes only BenchmarkTask — it does
not import benchmark-specific raw formats.

No external dependencies. No LLM calls. No data loading.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class BenchmarkTask:
    """Canonical task representation for ReliabilityHarness experiments.

    Fields
    ------
    task_id:
        Unique task identifier, e.g. "mbpp_1" or "HumanEval/0".
    benchmark:
        Benchmark name, e.g. "mbpp" or "humaneval".
    prompt:
        Natural-language problem description shown to the agent.
    entry_point:
        Function name the agent must implement (HumanEval style).
        None for benchmarks that do not specify an entry point (e.g. MBPP).
    tests:
        List of test assertion strings used to verify the generated solution.
    reference_solution:
        Ground-truth or canonical solution, used only for analysis — NOT
        passed to the agent.
    metadata:
        Arbitrary adapter-specific fields (source dataset split, difficulty
        tags, etc.). Never passed to the agent.
    """

    task_id: str
    benchmark: str
    prompt: str
    entry_point: Optional[str] = None
    tests: list[str] = field(default_factory=list)
    reference_solution: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict (for artifact writing)."""
        return {
            "task_id": self.task_id,
            "benchmark": self.benchmark,
            "prompt": self.prompt,
            "entry_point": self.entry_point,
            "tests": self.tests,
            "reference_solution": self.reference_solution,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "BenchmarkTask":
        """Deserialise from a plain dict."""
        return cls(
            task_id=d["task_id"],
            benchmark=d["benchmark"],
            prompt=d["prompt"],
            entry_point=d.get("entry_point"),
            tests=d.get("tests", []),
            reference_solution=d.get("reference_solution"),
            metadata=d.get("metadata", {}),
        )
