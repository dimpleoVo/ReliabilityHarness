"""
Tests for reliability_harness.runtime.generation.prompt_builder.

No LLM calls. No Docker. No .env reading. No output writes.
"""
import pytest

from reliability_harness.benchmarks.task_schema import BenchmarkTask
from reliability_harness.runtime.generation.prompt_builder import build_generation_prompt


def _make_task(**overrides):
    defaults = dict(
        task_id="test_task_1",
        benchmark="tiny",
        prompt="Write a function that adds two numbers.",
        entry_point="add",
        tests=["assert add(1, 2) == 3", "assert add(0, 0) == 0"],
        reference_solution="def add(a, b): return a + b",
    )
    defaults.update(overrides)
    return BenchmarkTask(**defaults)


class TestBuildGenerationPrompt:
    def test_returns_string(self):
        result = build_generation_prompt(_make_task())
        assert isinstance(result, str)

    def test_contains_task_prompt(self):
        result = build_generation_prompt(_make_task())
        assert "Write a function that adds two numbers." in result

    def test_contains_entry_point(self):
        result = build_generation_prompt(_make_task(entry_point="add"))
        assert "add" in result

    def test_does_not_contain_reference_solution(self):
        task = _make_task(reference_solution="def add(a, b): return a + b")
        result = build_generation_prompt(task)
        assert "def add(a, b): return a + b" not in result

    def test_requests_python_output(self):
        result = build_generation_prompt(_make_task())
        assert "python" in result.lower()

    def test_requests_code_block(self):
        result = build_generation_prompt(_make_task())
        assert "```python" in result or "```" in result

    def test_works_without_entry_point(self):
        task = _make_task(entry_point=None)
        result = build_generation_prompt(task)
        assert isinstance(result, str)
        assert "Write a function that adds two numbers." in result

    def test_works_without_reference_solution(self):
        task = _make_task(reference_solution=None)
        result = build_generation_prompt(task)
        assert isinstance(result, str)

    def test_works_with_empty_tests(self):
        task = _make_task(tests=[])
        result = build_generation_prompt(task)
        assert isinstance(result, str)

    def test_does_not_contain_none_reference_solution_string(self):
        task = _make_task(reference_solution=None)
        result = build_generation_prompt(task)
        assert "reference_solution" not in result

    def test_entry_point_label_present(self):
        task = _make_task(entry_point="my_func")
        result = build_generation_prompt(task)
        assert "my_func" in result
