"""
Root-level tests for reliability_harness.benchmarks.task_schema.BenchmarkTask.

Migration-4A/B: These tests constrain the canonical task schema for Benchmark-0.

No LLM calls. No Docker. No data loading. No ReActX/app/evalforge imports.
"""
from reliability_harness.benchmarks.task_schema import BenchmarkTask


class TestBenchmarkTaskFields:
    def test_required_fields(self):
        task = BenchmarkTask(task_id="mbpp_1", benchmark="mbpp", prompt="Write a fn.")
        assert task.task_id == "mbpp_1"
        assert task.benchmark == "mbpp"
        assert task.prompt == "Write a fn."

    def test_entry_point_default_is_none(self):
        task = BenchmarkTask(task_id="t1", benchmark="mbpp", prompt="p")
        assert task.entry_point is None

    def test_entry_point_can_be_set(self):
        task = BenchmarkTask(
            task_id="HumanEval/0",
            benchmark="humaneval",
            prompt="def has_close_elements(numbers, threshold):",
            entry_point="has_close_elements",
        )
        assert task.entry_point == "has_close_elements"

    def test_tests_default_is_empty_list(self):
        task = BenchmarkTask(task_id="t1", benchmark="mbpp", prompt="p")
        assert task.tests == []

    def test_tests_can_be_set(self):
        task = BenchmarkTask(
            task_id="mbpp_1",
            benchmark="mbpp",
            prompt="p",
            tests=["assert f(1) == 2", "assert f(0) == 0"],
        )
        assert len(task.tests) == 2
        assert "assert f(1) == 2" in task.tests

    def test_reference_solution_default_is_none(self):
        task = BenchmarkTask(task_id="t1", benchmark="mbpp", prompt="p")
        assert task.reference_solution is None

    def test_reference_solution_can_be_set(self):
        task = BenchmarkTask(
            task_id="t1",
            benchmark="mbpp",
            prompt="p",
            reference_solution="def f(x): return x + 1",
        )
        assert task.reference_solution == "def f(x): return x + 1"

    def test_metadata_default_is_empty_dict(self):
        task = BenchmarkTask(task_id="t1", benchmark="mbpp", prompt="p")
        assert task.metadata == {}

    def test_metadata_can_be_set(self):
        task = BenchmarkTask(
            task_id="t1",
            benchmark="mbpp",
            prompt="p",
            metadata={"split": "test", "difficulty": "easy"},
        )
        assert task.metadata["split"] == "test"
        assert task.metadata["difficulty"] == "easy"

    def test_metadata_instances_are_independent(self):
        t1 = BenchmarkTask(task_id="t1", benchmark="mbpp", prompt="p")
        t2 = BenchmarkTask(task_id="t2", benchmark="mbpp", prompt="p")
        t1.metadata["key"] = "val"
        assert "key" not in t2.metadata


class TestBenchmarkTaskSerialization:
    def test_to_dict_contains_all_fields(self):
        task = BenchmarkTask(
            task_id="mbpp_5",
            benchmark="mbpp",
            prompt="Write a sum fn.",
            entry_point=None,
            tests=["assert s([1,2]) == 3"],
            reference_solution="def s(l): return sum(l)",
            metadata={"source": "sanitized"},
        )
        d = task.to_dict()
        assert d["task_id"] == "mbpp_5"
        assert d["benchmark"] == "mbpp"
        assert d["prompt"] == "Write a sum fn."
        assert d["entry_point"] is None
        assert d["tests"] == ["assert s([1,2]) == 3"]
        assert d["reference_solution"] == "def s(l): return sum(l)"
        assert d["metadata"] == {"source": "sanitized"}

    def test_from_dict_roundtrip(self):
        original = BenchmarkTask(
            task_id="HumanEval/1",
            benchmark="humaneval",
            prompt="def separate_paren_groups(paren_string: str):",
            entry_point="separate_paren_groups",
            tests=["assert separate_paren_groups('( ) (( )) (( )( ))') == ['()', '(())', '(()())']"],
            reference_solution=None,
            metadata={},
        )
        restored = BenchmarkTask.from_dict(original.to_dict())
        assert restored.task_id == original.task_id
        assert restored.benchmark == original.benchmark
        assert restored.prompt == original.prompt
        assert restored.entry_point == original.entry_point
        assert restored.tests == original.tests
        assert restored.reference_solution == original.reference_solution
        assert restored.metadata == original.metadata

    def test_from_dict_optional_fields_default(self):
        d = {"task_id": "t1", "benchmark": "mbpp", "prompt": "hello"}
        task = BenchmarkTask.from_dict(d)
        assert task.entry_point is None
        assert task.tests == []
        assert task.reference_solution is None
        assert task.metadata == {}
