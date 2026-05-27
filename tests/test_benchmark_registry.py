"""
Root-level tests for reliability_harness.benchmarks.registry.

Migration-4A/B: These tests constrain the adapter registry for Benchmark-0.

No LLM calls. No Docker. No data loading. No ReActX/app/evalforge imports.
"""
import pytest

from reliability_harness.benchmarks.adapters.humaneval import HumanEvalAdapter
from reliability_harness.benchmarks.adapters.mbpp import MBPPAdapter
from reliability_harness.benchmarks.registry import get_adapter, list_benchmarks


class TestGetAdapter:
    def test_get_adapter_mbpp_returns_mbpp_adapter(self):
        adapter = get_adapter("mbpp")
        assert isinstance(adapter, MBPPAdapter)

    def test_get_adapter_humaneval_returns_humaneval_adapter(self):
        adapter = get_adapter("humaneval")
        assert isinstance(adapter, HumanEvalAdapter)

    def test_get_adapter_case_insensitive(self):
        assert isinstance(get_adapter("MBPP"), MBPPAdapter)
        assert isinstance(get_adapter("HumanEval"), HumanEvalAdapter)

    def test_get_adapter_unknown_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown benchmark"):
            get_adapter("swebench")

    def test_get_adapter_empty_string_raises_value_error(self):
        with pytest.raises(ValueError):
            get_adapter("")

    def test_get_adapter_returns_fresh_instance(self):
        a1 = get_adapter("mbpp")
        a2 = get_adapter("mbpp")
        assert a1 is not a2


class TestListBenchmarks:
    def test_list_benchmarks_contains_mbpp(self):
        assert "mbpp" in list_benchmarks()

    def test_list_benchmarks_contains_humaneval(self):
        assert "humaneval" in list_benchmarks()

    def test_list_benchmarks_is_sorted(self):
        result = list_benchmarks()
        assert result == sorted(result)
