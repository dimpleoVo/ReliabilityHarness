"""Tests for reliability_harness.runtime.execution.docker_runner.

Uses a fake backend — no Docker daemon required.
No LLM calls. No memory/retry imports. No .env reading.
"""
import pytest

from reliability_harness.runtime.execution.contract import ExecutionInput
from reliability_harness.runtime.execution.docker_runner import (
    DockerBackendResult,
    DockerExecutionBackend,
    execute_in_docker,
    _build_source,
)


# ── Fake backends ──────────────────────────────────────────────────────────────

class _SuccessBackend:
    def run_python(self, source_code: str, timeout_ms: int) -> DockerBackendResult:
        return DockerBackendResult(
            exit_code=0, stdout="", stderr="", timed_out=False, execution_time_ms=10
        )


class _AssertionFailureBackend:
    def run_python(self, source_code: str, timeout_ms: int) -> DockerBackendResult:
        return DockerBackendResult(
            exit_code=1,
            stdout="",
            stderr="Traceback (most recent call last):\n  ...\nAssertionError",
            timed_out=False,
            execution_time_ms=8,
        )


class _SyntaxErrorBackend:
    def run_python(self, source_code: str, timeout_ms: int) -> DockerBackendResult:
        return DockerBackendResult(
            exit_code=1,
            stdout="",
            stderr="  File '<stdin>', line 1\nSyntaxError: invalid syntax",
            timed_out=False,
            execution_time_ms=5,
        )


class _RuntimeErrorBackend:
    def run_python(self, source_code: str, timeout_ms: int) -> DockerBackendResult:
        return DockerBackendResult(
            exit_code=1,
            stdout="",
            stderr="Traceback (most recent call last):\n  ...\nValueError: boom",
            timed_out=False,
            execution_time_ms=9,
        )


class _TimeoutBackend:
    def run_python(self, source_code: str, timeout_ms: int) -> DockerBackendResult:
        return DockerBackendResult(
            exit_code=None, stdout="", stderr="", timed_out=True, execution_time_ms=timeout_ms
        )


class _ExceptionBackend:
    def run_python(self, source_code: str, timeout_ms: int) -> DockerBackendResult:
        raise RuntimeError("Docker daemon not reachable")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_input(**kwargs) -> ExecutionInput:
    defaults = dict(
        run_id="run_4b_001",
        benchmark="mbpp",
        task_id="mbpp_1",
        candidate_code="def add(a, b): return a + b",
        tests=["assert add(1, 2) == 3"],
        timeout_ms=3000,
    )
    defaults.update(kwargs)
    return ExecutionInput(**defaults)


# ── Tests: success ─────────────────────────────────────────────────────────────

class TestDockerSuccess:
    def test_tests_passed_true(self):
        result = execute_in_docker(_make_input(), backend=_SuccessBackend())
        assert result.tests_passed is True

    def test_exit_code_zero(self):
        result = execute_in_docker(_make_input(), backend=_SuccessBackend())
        assert result.exit_code == 0

    def test_error_type_none(self):
        result = execute_in_docker(_make_input(), backend=_SuccessBackend())
        assert result.error_type is None

    def test_timed_out_false(self):
        result = execute_in_docker(_make_input(), backend=_SuccessBackend())
        assert result.timed_out is False


# ── Tests: docker_used / execution_performed invariants ───────────────────────

class TestDockerInvariants:
    def test_docker_used_true_on_success(self):
        result = execute_in_docker(_make_input(), backend=_SuccessBackend())
        assert result.docker_used is True

    def test_docker_used_true_on_failure(self):
        result = execute_in_docker(_make_input(), backend=_AssertionFailureBackend())
        assert result.docker_used is True

    def test_docker_used_true_on_timeout(self):
        result = execute_in_docker(_make_input(), backend=_TimeoutBackend())
        assert result.docker_used is True

    def test_docker_used_true_on_infra_error(self):
        result = execute_in_docker(_make_input(), backend=_ExceptionBackend())
        assert result.docker_used is True

    def test_execution_performed_true_on_success(self):
        result = execute_in_docker(_make_input(), backend=_SuccessBackend())
        assert result.execution_performed is True

    def test_execution_performed_true_on_failure(self):
        result = execute_in_docker(_make_input(), backend=_AssertionFailureBackend())
        assert result.execution_performed is True

    def test_execution_performed_true_on_infra_error(self):
        result = execute_in_docker(_make_input(), backend=_ExceptionBackend())
        assert result.execution_performed is True


# ── Tests: error_type mapping ──────────────────────────────────────────────────

class TestDockerErrorMapping:
    def test_assertion_failure_error_type(self):
        result = execute_in_docker(_make_input(), backend=_AssertionFailureBackend())
        assert result.error_type == "assertion_failure"

    def test_assertion_failure_tests_passed_false(self):
        result = execute_in_docker(_make_input(), backend=_AssertionFailureBackend())
        assert result.tests_passed is False

    def test_syntax_error_error_type(self):
        result = execute_in_docker(_make_input(), backend=_SyntaxErrorBackend())
        assert result.error_type == "syntax_error"

    def test_syntax_error_tests_passed_false(self):
        result = execute_in_docker(_make_input(), backend=_SyntaxErrorBackend())
        assert result.tests_passed is False

    def test_runtime_error_error_type(self):
        result = execute_in_docker(_make_input(), backend=_RuntimeErrorBackend())
        assert result.error_type == "runtime_error"

    def test_runtime_error_tests_passed_false(self):
        result = execute_in_docker(_make_input(), backend=_RuntimeErrorBackend())
        assert result.tests_passed is False

    def test_timeout_error_type(self):
        result = execute_in_docker(_make_input(), backend=_TimeoutBackend())
        assert result.error_type == "timeout"

    def test_timeout_timed_out_true(self):
        result = execute_in_docker(_make_input(), backend=_TimeoutBackend())
        assert result.timed_out is True

    def test_timeout_tests_passed_false(self):
        result = execute_in_docker(_make_input(), backend=_TimeoutBackend())
        assert result.tests_passed is False

    def test_backend_exception_infrastructure_error(self):
        result = execute_in_docker(_make_input(), backend=_ExceptionBackend())
        assert result.error_type == "infrastructure_error"

    def test_backend_exception_tests_passed_false(self):
        result = execute_in_docker(_make_input(), backend=_ExceptionBackend())
        assert result.tests_passed is False

    def test_backend_exception_exit_code_none(self):
        result = execute_in_docker(_make_input(), backend=_ExceptionBackend())
        assert result.exit_code is None


# ── Tests: identity propagation ────────────────────────────────────────────────

class TestDockerIdentityPropagation:
    def test_run_id_propagated(self):
        result = execute_in_docker(_make_input(run_id="my_run"), backend=_SuccessBackend())
        assert result.run_id == "my_run"

    def test_benchmark_propagated(self):
        result = execute_in_docker(_make_input(benchmark="humaneval"), backend=_SuccessBackend())
        assert result.benchmark == "humaneval"

    def test_task_id_propagated(self):
        result = execute_in_docker(_make_input(task_id="HumanEval/42"), backend=_SuccessBackend())
        assert result.task_id == "HumanEval/42"

    def test_run_id_propagated_on_infra_error(self):
        result = execute_in_docker(_make_input(run_id="fail_run"), backend=_ExceptionBackend())
        assert result.run_id == "fail_run"


# ── Tests: source generation ───────────────────────────────────────────────────

class TestDockerSourceGeneration:
    def test_source_contains_candidate_code(self):
        inp = _make_input(
            candidate_code="def multiply(a, b): return a * b",
            tests=["assert multiply(2, 3) == 6"],
        )
        source = _build_source(inp)
        assert "def multiply(a, b): return a * b" in source

    def test_source_contains_tests(self):
        inp = _make_input(
            candidate_code="def f(): return 1",
            tests=["assert f() == 1", "assert f() != 0"],
        )
        source = _build_source(inp)
        assert "assert f() == 1" in source
        assert "assert f() != 0" in source

    class _CapturingBackend:
        def __init__(self):
            self.last_source = None

        def run_python(self, source_code: str, timeout_ms: int) -> DockerBackendResult:
            self.last_source = source_code
            return DockerBackendResult(
                exit_code=0, stdout="", stderr="", timed_out=False, execution_time_ms=5
            )

    def test_backend_receives_combined_source(self):
        capturing = self._CapturingBackend()
        inp = _make_input(
            candidate_code="def f(): return 99",
            tests=["assert f() == 99"],
        )
        execute_in_docker(inp, backend=capturing)
        assert "def f(): return 99" in capturing.last_source
        assert "assert f() == 99" in capturing.last_source


# ── Tests: no secrets ─────────────────────────────────────────────────────────

class TestDockerNoSecrets:
    def test_no_api_key_in_result_stderr(self):
        result = execute_in_docker(_make_input(), backend=_ExceptionBackend())
        assert "api_key" not in result.stderr.lower()
        assert "sk-" not in result.stderr

    def test_no_deepseek_in_module(self):
        import reliability_harness.runtime.execution.docker_runner as m
        src = open(m.__file__, encoding="utf-8").read()
        assert "deepseek" not in src.lower()
        assert "DEEPSEEK_API_KEY" not in src


# ── Tests: no forbidden imports ───────────────────────────────────────────────

def _collect_imports(src: str) -> set[str]:
    """Return the set of all module/name strings that appear in actual import
    statements in *src*.  Docstrings and comments are excluded because ast.parse
    only sees syntactic import nodes, not string literals.
    """
    import ast
    tree = ast.parse(src)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
            for alias in node.names:
                names.add(alias.name)
    return names


class TestDockerNoForbiddenImports:
    @staticmethod
    def _imports() -> set[str]:
        import reliability_harness.runtime.execution.docker_runner as m
        src = open(m.__file__, encoding="utf-8").read()
        return _collect_imports(src)

    def test_no_llm_import(self):
        imports = self._imports()
        forbidden = {"LLMClient", "llm_client", "reliability_harness.core.llm"}
        assert imports.isdisjoint(forbidden), f"Forbidden LLM import found: {imports & forbidden}"

    def test_no_memory_import(self):
        imports = self._imports()
        assert not any(
            "reliability_harness.memory" in name for name in imports
        ), f"Forbidden memory import found in: {imports}"

    def test_no_retry_import(self):
        imports = self._imports()
        assert not any(
            "retry_controller" in name for name in imports
        ), f"Forbidden retry import found in: {imports}"

    def test_no_closed_loop_runner_import(self):
        imports = self._imports()
        assert not any(
            "closed_loop_runner" in name for name in imports
        ), f"Forbidden closed_loop_runner import found in: {imports}"

    def test_no_code_execution_tool_import(self):
        imports = self._imports()
        assert not any(
            "CodeExecutionTool" in name or "code_executor" in name for name in imports
        ), f"Forbidden CodeExecutionTool import found in: {imports}"


# ── Tests: DockerExecutionBackend protocol ────────────────────────────────────

class TestDockerBackendProtocol:
    def test_fake_backend_satisfies_protocol(self):
        assert isinstance(_SuccessBackend(), DockerExecutionBackend)

    def test_fake_timeout_backend_satisfies_protocol(self):
        assert isinstance(_TimeoutBackend(), DockerExecutionBackend)
