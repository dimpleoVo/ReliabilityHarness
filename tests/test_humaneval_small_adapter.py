"""
Tests for HumanEvalAdapter with small fixture (Benchmark-2).

No LLM calls. No Docker. No sandbox. No output writes.
"""
import pytest

from reliability_harness.benchmarks.adapters.humaneval import HumanEvalAdapter
from reliability_harness.benchmarks.task_schema import BenchmarkTask


class TestHumanEvalSmallAdapter:
    def setup_method(self):
        self.adapter = HumanEvalAdapter()

    def test_load_tasks_returns_list(self):
        tasks = self.adapter.load_tasks()
        assert isinstance(tasks, list)

    def test_load_tasks_returns_benchmark_task_instances(self):
        tasks = self.adapter.load_tasks()
        for task in tasks:
            assert isinstance(task, BenchmarkTask)

    def test_load_tasks_at_least_two(self):
        tasks = self.adapter.load_tasks()
        assert len(tasks) >= 2

    def test_load_tasks_limit_one(self):
        tasks = self.adapter.load_tasks(limit=1)
        assert len(tasks) == 1

    def test_task_benchmark_is_humaneval(self):
        tasks = self.adapter.load_tasks()
        for task in tasks:
            assert task.benchmark == "humaneval"

    def test_task_id_nonempty(self):
        tasks = self.adapter.load_tasks()
        for task in tasks:
            assert task.task_id

    def test_task_prompt_nonempty(self):
        tasks = self.adapter.load_tasks()
        for task in tasks:
            assert task.prompt

    def test_task_entry_point_nonempty(self):
        tasks = self.adapter.load_tasks()
        for task in tasks:
            assert task.entry_point

    def test_task_tests_is_nonempty_list(self):
        tasks = self.adapter.load_tasks()
        for task in tasks:
            assert isinstance(task.tests, list)
            assert len(task.tests) > 0

    def test_task_reference_solution_nonempty(self):
        tasks = self.adapter.load_tasks()
        for task in tasks:
            assert task.reference_solution

    def test_task_metadata_has_source(self):
        tasks = self.adapter.load_tasks()
        for task in tasks:
            assert "source" in task.metadata

    def test_task_metadata_has_split(self):
        tasks = self.adapter.load_tasks()
        for task in tasks:
            assert "split" in task.metadata

    def test_normalize_returns_benchmark_task(self):
        raw = {
            "task_id": "HumanEval/test",
            "benchmark": "humaneval",
            "prompt": "def test_fn():\n    \"\"\"Test.\"\"\"\n",
            "entry_point": "test_fn",
            "tests": ["assert test_fn() == 1"],
            "reference_solution": "def test_fn(): return 1",
            "metadata": {
                "source": "humaneval_small_fixture",
                "split": "test",
            },
        }
        result = self.adapter.normalize(raw)
        assert isinstance(result, BenchmarkTask)

    def test_normalize_does_not_write_outputs(self, tmp_path):
        raw = {
            "task_id": "HumanEval/test",
            "benchmark": "humaneval",
            "prompt": "def test_fn():\n    \"\"\"Test.\"\"\"\n",
            "entry_point": "test_fn",
            "tests": ["assert test_fn() == 1"],
            "reference_solution": "def test_fn(): return 1",
            "metadata": {
                "source": "humaneval_small_fixture",
                "split": "test",
            },
        }
        before = list(tmp_path.iterdir())
        self.adapter.normalize(raw)
        after = list(tmp_path.iterdir())
        assert before == after
