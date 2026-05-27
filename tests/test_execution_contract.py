"""Tests for reliability_harness.runtime.execution.contract.

No LLM calls. No Docker. No .env reading.
"""
import pytest
from reliability_harness.runtime.execution.contract import ExecutionInput, ExecutionResult


class TestExecutionInput:
    def test_required_fields_present(self):
        inp = ExecutionInput(
            run_id="r1",
            benchmark="mbpp",
            task_id="mbpp_1",
            candidate_code="def add(a, b): return a + b",
            tests=["assert add(1, 2) == 3"],
        )
        assert inp.run_id == "r1"
        assert inp.benchmark == "mbpp"
        assert inp.task_id == "mbpp_1"
        assert inp.candidate_code == "def add(a, b): return a + b"
        assert inp.tests == ["assert add(1, 2) == 3"]

    def test_timeout_ms_default(self):
        inp = ExecutionInput(
            run_id="r1", benchmark="mbpp", task_id="t1",
            candidate_code="pass", tests=[],
        )
        assert inp.timeout_ms == 1000

    def test_docker_used_default_false(self):
        inp = ExecutionInput(
            run_id="r1", benchmark="mbpp", task_id="t1",
            candidate_code="pass", tests=[],
        )
        assert inp.docker_used is False

    def test_source_generation_artifact_default_none(self):
        inp = ExecutionInput(
            run_id="r1", benchmark="mbpp", task_id="t1",
            candidate_code="pass", tests=[],
        )
        assert inp.source_generation_artifact is None

    def test_source_generation_artifact_set(self):
        inp = ExecutionInput(
            run_id="r1", benchmark="mbpp", task_id="t1",
            candidate_code="pass", tests=[],
            source_generation_artifact="outputs/predictions/run_001/mbpp_1.json",
        )
        assert inp.source_generation_artifact == "outputs/predictions/run_001/mbpp_1.json"

    def test_tests_is_list(self):
        inp = ExecutionInput(
            run_id="r1", benchmark="mbpp", task_id="t1",
            candidate_code="pass",
            tests=["assert True", "assert 1 == 1"],
        )
        assert isinstance(inp.tests, list)
        assert len(inp.tests) == 2


class TestExecutionResult:
    def _make_result(self, **kwargs):
        defaults = dict(
            run_id="r1",
            benchmark="mbpp",
            task_id="t1",
            exit_code=0,
            stdout="",
            stderr="",
            timed_out=False,
            tests_passed=True,
            error_type=None,
            execution_time_ms=12,
            docker_used=False,
            execution_performed=True,
        )
        defaults.update(kwargs)
        return ExecutionResult(**defaults)

    def test_required_fields_present(self):
        r = self._make_result()
        assert r.run_id == "r1"
        assert r.benchmark == "mbpp"
        assert r.task_id == "t1"
        assert r.exit_code == 0
        assert r.stdout == ""
        assert r.stderr == ""
        assert r.timed_out is False
        assert r.tests_passed is True
        assert r.error_type is None
        assert r.execution_time_ms == 12
        assert r.docker_used is False
        assert r.execution_performed is True

    def test_docker_used_is_false_by_contract(self):
        r = self._make_result(docker_used=False)
        assert r.docker_used is False

    def test_execution_performed_is_true_by_contract(self):
        r = self._make_result(execution_performed=True)
        assert r.execution_performed is True

    def test_exit_code_none_on_timeout(self):
        r = self._make_result(exit_code=None, timed_out=True, tests_passed=False, error_type="timeout")
        assert r.exit_code is None
        assert r.timed_out is True

    def test_error_type_none_on_success(self):
        r = self._make_result(tests_passed=True, error_type=None)
        assert r.error_type is None
