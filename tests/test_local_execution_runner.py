"""Tests for reliability_harness.runtime.execution.local_runner.

No LLM calls. No Docker. No .env reading.
Uses only trusted fixture code — local runner is not safe for untrusted input.
"""
import pytest
from reliability_harness.runtime.execution.contract import ExecutionInput
from reliability_harness.runtime.execution.local_runner import execute_locally


def _make_input(**kwargs) -> ExecutionInput:
    defaults = dict(
        run_id="test_run",
        benchmark="mbpp",
        task_id="mbpp_test",
        candidate_code="def add(a, b): return a + b",
        tests=["assert add(1, 2) == 3"],
        timeout_ms=3000,
    )
    defaults.update(kwargs)
    return ExecutionInput(**defaults)


class TestPassingCode:
    def test_tests_passed_true(self):
        inp = _make_input(
            candidate_code="def add(a, b): return a + b",
            tests=["assert add(1, 2) == 3", "assert add(0, 0) == 0"],
        )
        result = execute_locally(inp)
        assert result.tests_passed is True

    def test_exit_code_zero(self):
        inp = _make_input(
            candidate_code="def add(a, b): return a + b",
            tests=["assert add(2, 3) == 5"],
        )
        result = execute_locally(inp)
        assert result.exit_code == 0

    def test_error_type_none(self):
        inp = _make_input(
            candidate_code="def square(n): return n * n",
            tests=["assert square(4) == 16"],
        )
        result = execute_locally(inp)
        assert result.error_type is None

    def test_timed_out_false(self):
        inp = _make_input(
            candidate_code="def f(): return 1",
            tests=["assert f() == 1"],
        )
        result = execute_locally(inp)
        assert result.timed_out is False


class TestFailingAssertion:
    def test_tests_passed_false(self):
        inp = _make_input(
            candidate_code="def add(a, b): return a - b",
            tests=["assert add(1, 2) == 3"],
        )
        result = execute_locally(inp)
        assert result.tests_passed is False

    def test_error_type_assertion_failure(self):
        inp = _make_input(
            candidate_code="def add(a, b): return 0",
            tests=["assert add(1, 2) == 3"],
        )
        result = execute_locally(inp)
        assert result.error_type == "assertion_failure"

    def test_exit_code_nonzero(self):
        inp = _make_input(
            candidate_code="def f(): return 99",
            tests=["assert f() == 0"],
        )
        result = execute_locally(inp)
        assert result.exit_code != 0


class TestSyntaxError:
    def test_error_type_syntax_error(self):
        inp = _make_input(
            candidate_code="def broken(\n    # unclosed",
            tests=["assert True"],
        )
        result = execute_locally(inp)
        assert result.error_type == "syntax_error"

    def test_tests_passed_false_on_syntax_error(self):
        inp = _make_input(
            candidate_code="def broken(\n    # unclosed",
            tests=["assert True"],
        )
        result = execute_locally(inp)
        assert result.tests_passed is False


class TestRuntimeError:
    def test_error_type_runtime_error(self):
        inp = _make_input(
            candidate_code="def f(): raise ValueError('boom')",
            tests=["f()"],
        )
        result = execute_locally(inp)
        assert result.error_type == "runtime_error"

    def test_tests_passed_false_on_runtime_error(self):
        inp = _make_input(
            candidate_code="def f(): raise ValueError('boom')",
            tests=["f()"],
        )
        result = execute_locally(inp)
        assert result.tests_passed is False


class TestTimeout:
    def test_timed_out_true(self):
        inp = _make_input(
            candidate_code="import time\ndef f(): time.sleep(10)",
            tests=["f()"],
            timeout_ms=100,
        )
        result = execute_locally(inp)
        assert result.timed_out is True

    def test_error_type_timeout(self):
        inp = _make_input(
            candidate_code="import time\ndef f(): time.sleep(10)",
            tests=["f()"],
            timeout_ms=100,
        )
        result = execute_locally(inp)
        assert result.error_type == "timeout"

    def test_tests_passed_false_on_timeout(self):
        inp = _make_input(
            candidate_code="import time\ndef f(): time.sleep(10)",
            tests=["f()"],
            timeout_ms=100,
        )
        result = execute_locally(inp)
        assert result.tests_passed is False


class TestContractInvariants:
    def test_docker_used_always_false(self):
        inp = _make_input(
            candidate_code="def f(): return 1",
            tests=["assert f() == 1"],
        )
        result = execute_locally(inp)
        assert result.docker_used is False

    def test_execution_performed_always_true(self):
        inp = _make_input(
            candidate_code="def f(): return 1",
            tests=["assert f() == 1"],
        )
        result = execute_locally(inp)
        assert result.execution_performed is True

    def test_run_id_propagated(self):
        inp = _make_input(run_id="propagation_check")
        result = execute_locally(inp)
        assert result.run_id == "propagation_check"

    def test_benchmark_propagated(self):
        inp = _make_input(benchmark="humaneval")
        result = execute_locally(inp)
        assert result.benchmark == "humaneval"

    def test_task_id_propagated(self):
        inp = _make_input(task_id="HumanEval/42")
        result = execute_locally(inp)
        assert result.task_id == "HumanEval/42"

    def test_no_llm_import(self):
        import reliability_harness.runtime.execution.local_runner as m
        src = open(m.__file__, encoding="utf-8").read()
        assert "llm_client" not in src.lower()
        assert "LLMClient" not in src
        assert "openai" not in src.lower()
        assert "deepseek" not in src.lower()
