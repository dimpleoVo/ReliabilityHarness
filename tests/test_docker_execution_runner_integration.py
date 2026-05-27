"""Optional Docker integration tests — Benchmark-4B.1.

Marked pytest.mark.docker — skipped by default.
Requires a running Docker daemon and the python:3.11-slim image.

NOT included in scripts/run_tests.sh.
Run manually:
  pytest -m docker tests/test_docker_execution_runner_integration.py -v
"""
import pytest

from reliability_harness.runtime.execution.contract import ExecutionInput
from reliability_harness.runtime.execution.docker_runner import execute_in_docker


@pytest.mark.docker
class TestDockerIntegration:
    def _make_input(self, **kwargs) -> ExecutionInput:
        defaults = dict(
            run_id="integration_run",
            benchmark="mbpp",
            task_id="mbpp_integration",
            candidate_code="def add(a, b): return a + b",
            tests=["assert add(1, 2) == 3"],
            timeout_ms=10000,
        )
        defaults.update(kwargs)
        return ExecutionInput(**defaults)

    def test_passing_code_in_docker(self):
        result = execute_in_docker(self._make_input())
        assert result.tests_passed is True
        assert result.docker_used is True
        assert result.execution_performed is True

    def test_failing_assertion_in_docker(self):
        inp = self._make_input(
            candidate_code="def add(a, b): return 0",
            tests=["assert add(1, 2) == 3"],
        )
        result = execute_in_docker(inp)
        assert result.tests_passed is False
        assert result.error_type == "assertion_failure"
        assert result.docker_used is True

    def test_syntax_error_in_docker(self):
        inp = self._make_input(
            candidate_code="def broken(\n    # unclosed",
            tests=["assert True"],
        )
        result = execute_in_docker(inp)
        assert result.error_type == "syntax_error"
        assert result.docker_used is True
