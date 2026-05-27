"""
Prompt builder for generation-only LLM candidate generation.

Pure transformation: BenchmarkTask -> prompt string.
No LLM calls. No side effects. No import-time initialization.
"""
from __future__ import annotations

from reliability_harness.benchmarks.task_schema import BenchmarkTask


def build_generation_prompt(task: BenchmarkTask) -> str:
    """Build a generation prompt from a BenchmarkTask.

    The prompt asks the LLM to output a Python solution inside a ```python
    code block. It includes the task prompt and entry_point information.
    It never includes reference_solution.
    """
    lines = [
        "You are an expert Python programmer.",
        "",
        "Write a Python solution for the following problem.",
        "Wrap your complete solution in a ```python ... ``` code block.",
        "Do not include any explanation outside the code block.",
        "",
        "## Problem",
        "",
        task.prompt,
    ]

    if task.entry_point:
        lines += [
            "",
            "## Entry Point",
            "",
            f"Your solution must define a function named `{task.entry_point}`.",
        ]

    if task.tests:
        lines += [
            "",
            "## Specification (your solution must satisfy these assertions)",
            "",
        ]
        for test in task.tests:
            lines.append(f"    {test}")

    return "\n".join(lines)
