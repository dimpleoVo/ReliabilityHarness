"""
Focused tests for TinyFixtureAdapter.

No LLM calls. No Docker. No network. No sandbox.
Reads only from data/fixtures/tiny_code_tasks.json.
"""
import pytest

from reliability_harness.benchmarks.adapters.tiny import TinyFixtureAdapter
from reliability_harness.benchmarks.task_schema import BenchmarkTask


class TestTinyFixtureAdapterLoadTasks:
    def test_load_tasks_returns_list(self):
        adapter = TinyFixtureAdapter()
        tasks = adapter.load_tasks()
        assert isinstance(tasks, list)

    def test_load_tasks_returns_benchmark_task_instances(self):
        adapter = TinyFixtureAdapter()
        tasks = adapter.load_tasks()
        assert all(isinstance(t, BenchmarkTask) for t in tasks)

    def test_load_tasks_at_least_two_tasks(self):
        adapter = TinyFixtureAdapter()
        tasks = adapter.load_tasks()
        assert len(tasks) >= 2

    def test_load_tasks_limit_one(self):
        adapter = TinyFixtureAdapter()
        tasks = adapter.load_tasks(limit=1)
        assert len(tasks) == 1

    def test_load_tasks_limit_respects_max(self):
        adapter = TinyFixtureAdapter()
        all_tasks = adapter.load_tasks()
        limited = adapter.load_tasks(limit=1)
        assert len(limited) <= len(all_tasks)

    def test_all_tasks_benchmark_is_tiny(self):
        adapter = TinyFixtureAdapter()
        tasks = adapter.load_tasks()
        assert all(t.benchmark == "tiny" for t in tasks)

    def test_all_tasks_have_task_id(self):
        adapter = TinyFixtureAdapter()
        tasks = adapter.load_tasks()
        assert all(bool(t.task_id) for t in tasks)

    def test_all_tasks_have_prompt(self):
        adapter = TinyFixtureAdapter()
        tasks = adapter.load_tasks()
        assert all(bool(t.prompt) for t in tasks)

    def test_all_tasks_have_entry_point(self):
        adapter = TinyFixtureAdapter()
        tasks = adapter.load_tasks()
        assert all(t.entry_point is not None for t in tasks)

    def test_all_tasks_tests_is_list(self):
        adapter = TinyFixtureAdapter()
        tasks = adapter.load_tasks()
        assert all(isinstance(t.tests, list) for t in tasks)

    def test_all_tasks_have_at_least_one_test(self):
        adapter = TinyFixtureAdapter()
        tasks = adapter.load_tasks()
        assert all(len(t.tests) > 0 for t in tasks)

    def test_split_test_default_works(self):
        adapter = TinyFixtureAdapter()
        tasks = adapter.load_tasks(split="test")
        assert len(tasks) >= 2

    def test_adapter_name(self):
        assert TinyFixtureAdapter.name == "tiny"


class TestTinyFixtureAdapterNormalize:
    def _raw(self, **overrides):
        base = {
            "task_id": "tiny_test",
            "benchmark": "tiny",
            "prompt": "Write a function",
            "entry_point": "fn",
            "tests": ["assert fn() == 1"],
            "reference_solution": "def fn(): return 1",
            "metadata": {},
        }
        base.update(overrides)
        return base

    def test_normalize_returns_benchmark_task(self):
        adapter = TinyFixtureAdapter()
        task = adapter.normalize(self._raw())
        assert isinstance(task, BenchmarkTask)

    def test_normalize_maps_task_id(self):
        adapter = TinyFixtureAdapter()
        task = adapter.normalize(self._raw(task_id="tiny_xyz"))
        assert task.task_id == "tiny_xyz"

    def test_normalize_maps_benchmark(self):
        adapter = TinyFixtureAdapter()
        task = adapter.normalize(self._raw())
        assert task.benchmark == "tiny"

    def test_normalize_maps_prompt(self):
        adapter = TinyFixtureAdapter()
        task = adapter.normalize(self._raw(prompt="Do something"))
        assert task.prompt == "Do something"

    def test_normalize_maps_entry_point(self):
        adapter = TinyFixtureAdapter()
        task = adapter.normalize(self._raw(entry_point="my_fn"))
        assert task.entry_point == "my_fn"

    def test_normalize_maps_tests(self):
        adapter = TinyFixtureAdapter()
        tests = ["assert fn(1) == 2", "assert fn(0) == 0"]
        task = adapter.normalize(self._raw(tests=tests))
        assert task.tests == tests

    def test_normalize_maps_reference_solution(self):
        adapter = TinyFixtureAdapter()
        task = adapter.normalize(self._raw(reference_solution="def fn(): pass"))
        assert task.reference_solution == "def fn(): pass"

    def test_normalize_maps_metadata(self):
        adapter = TinyFixtureAdapter()
        meta = {"difficulty": "easy", "split": "test"}
        task = adapter.normalize(self._raw(metadata=meta))
        assert task.metadata == meta

    def test_normalize_entry_point_optional(self):
        adapter = TinyFixtureAdapter()
        raw = self._raw()
        raw.pop("entry_point")
        task = adapter.normalize(raw)
        assert task.entry_point is None

    def test_normalize_tests_defaults_to_empty_list(self):
        adapter = TinyFixtureAdapter()
        raw = self._raw()
        raw.pop("tests")
        task = adapter.normalize(raw)
        assert task.tests == []
