"""Tests for reliability_harness.runtime.execution.integration.

Uses fake Docker backend and tmp_path for artifacts.
No real Docker daemon. No real LLM. No real DeepSeek artifacts.
No full MBPP/HumanEval run.

Fixture: benchmark="tiny", task_id="tiny_001"
  (loaded from data/fixtures/tiny_code_tasks.json — always available)
"""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from reliability_harness.runtime.execution.docker_runner import DockerBackendResult
from reliability_harness.runtime.execution.integration import (
    ExecutionIntegrationError,
    execute_generation_artifact,
)


# ── Fake backends ──────────────────────────────────────────────────────────────

class _SuccessBackend:
    def run_python(self, source_code: str, timeout_ms: int) -> DockerBackendResult:
        return DockerBackendResult(
            exit_code=0, stdout="", stderr="", timed_out=False, execution_time_ms=7
        )


class _FailureBackend:
    def run_python(self, source_code: str, timeout_ms: int) -> DockerBackendResult:
        return DockerBackendResult(
            exit_code=1,
            stdout="",
            stderr="AssertionError",
            timed_out=False,
            execution_time_ms=6,
        )


class _NeverCalledBackend:
    """Raises if the backend is invoked — used to assert backend is not reached."""
    def run_python(self, source_code: str, timeout_ms: int) -> DockerBackendResult:
        raise AssertionError("Backend must not be called in this test path")


# ── Fixture helper ─────────────────────────────────────────────────────────────

def _write_gen_artifact(tmp_path: Path, **overrides) -> Path:
    """Write a fake generation artifact JSON and return its path."""
    data: dict = {
        "run_id": "run_4c_test",
        "benchmark": "tiny",
        "task_id": "tiny_001",
        "model_name": "deepseek-chat",
        "extraction_status": "success",
        "extracted_code": "def add(a, b): return a + b",
        "prompt": "Write an add function.",
        "raw_response": "```python\ndef add(a, b): return a + b\n```",
        "error": None,
        "timestamp": "2026-01-01T00:00:00+00:00",
        "llm_used": True,
        "docker_used": False,
        "execution_performed": False,
    }
    data.update(overrides)
    path = tmp_path / "gen_artifact.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ── 1. Happy path: valid artifact -> summary + artifact written ────────────────

class TestExecutionIntegrationHappyPath:
    def test_returns_summary_dict(self, tmp_path):
        path = _write_gen_artifact(tmp_path)
        summary = execute_generation_artifact(
            path,
            output_root=tmp_path / "executions",
            backend=_SuccessBackend(),
        )
        assert isinstance(summary, dict)

    def test_summary_has_generation_artifact_path(self, tmp_path):
        path = _write_gen_artifact(tmp_path)
        summary = execute_generation_artifact(
            path,
            output_root=tmp_path / "executions",
            backend=_SuccessBackend(),
        )
        assert "generation_artifact_path" in summary
        assert str(path) == summary["generation_artifact_path"]

    def test_summary_has_execution_artifact_path(self, tmp_path):
        path = _write_gen_artifact(tmp_path)
        summary = execute_generation_artifact(
            path,
            output_root=tmp_path / "executions",
            backend=_SuccessBackend(),
        )
        assert "execution_artifact_path" in summary
        assert Path(summary["execution_artifact_path"]).exists()

    def test_summary_benchmark(self, tmp_path):
        path = _write_gen_artifact(tmp_path)
        summary = execute_generation_artifact(
            path,
            output_root=tmp_path / "executions",
            backend=_SuccessBackend(),
        )
        assert summary["benchmark"] == "tiny"

    def test_summary_task_id(self, tmp_path):
        path = _write_gen_artifact(tmp_path)
        summary = execute_generation_artifact(
            path,
            output_root=tmp_path / "executions",
            backend=_SuccessBackend(),
        )
        assert summary["task_id"] == "tiny_001"

    def test_summary_tests_passed(self, tmp_path):
        path = _write_gen_artifact(tmp_path)
        summary = execute_generation_artifact(
            path,
            output_root=tmp_path / "executions",
            backend=_SuccessBackend(),
        )
        assert summary["tests_passed"] is True

    def test_summary_error_type_none_on_success(self, tmp_path):
        path = _write_gen_artifact(tmp_path)
        summary = execute_generation_artifact(
            path,
            output_root=tmp_path / "executions",
            backend=_SuccessBackend(),
        )
        assert summary["error_type"] is None

    def test_summary_model_name(self, tmp_path):
        path = _write_gen_artifact(tmp_path)
        summary = execute_generation_artifact(
            path,
            output_root=tmp_path / "executions",
            backend=_SuccessBackend(),
        )
        assert summary["model_name"] == "deepseek-chat"

    def test_summary_extraction_status(self, tmp_path):
        path = _write_gen_artifact(tmp_path)
        summary = execute_generation_artifact(
            path,
            output_root=tmp_path / "executions",
            backend=_SuccessBackend(),
        )
        assert summary["extraction_status"] == "success"


# ── 2. source_generation_artifact preserved in execution artifact ──────────────

class TestSourceArtifactPreservation:
    def test_execution_artifact_contains_source_generation_artifact(self, tmp_path):
        gen_path = _write_gen_artifact(tmp_path)
        summary = execute_generation_artifact(
            gen_path,
            output_root=tmp_path / "executions",
            backend=_SuccessBackend(),
        )
        exec_artifact_path = Path(summary["execution_artifact_path"])
        with open(exec_artifact_path, encoding="utf-8") as f:
            artifact = json.load(f)
        assert artifact.get("source_generation_artifact") == str(gen_path)

    def test_execution_artifact_has_result_block(self, tmp_path):
        gen_path = _write_gen_artifact(tmp_path)
        summary = execute_generation_artifact(
            gen_path,
            output_root=tmp_path / "executions",
            backend=_SuccessBackend(),
        )
        with open(summary["execution_artifact_path"], encoding="utf-8") as f:
            artifact = json.load(f)
        assert "result" in artifact
        assert "tests_passed" in artifact["result"]

    def test_execution_artifact_run_id_suffix(self, tmp_path):
        gen_path = _write_gen_artifact(tmp_path, run_id="my_gen_run")
        summary = execute_generation_artifact(
            gen_path,
            output_root=tmp_path / "executions",
            backend=_SuccessBackend(),
        )
        assert summary["run_id"] == "my_gen_run_exec"


# ── 3. Validation errors — backend must not be called ─────────────────────────

class TestValidationErrors:
    def test_extraction_status_not_success_raises(self, tmp_path):
        path = _write_gen_artifact(tmp_path, extraction_status="no_code_block")
        with pytest.raises(ExecutionIntegrationError, match="extraction_status"):
            execute_generation_artifact(
                path,
                output_root=tmp_path / "executions",
                backend=_NeverCalledBackend(),
            )

    def test_extraction_status_failure_backend_not_called(self, tmp_path):
        path = _write_gen_artifact(tmp_path, extraction_status="no_code_block")
        with pytest.raises(ExecutionIntegrationError):
            execute_generation_artifact(
                path,
                output_root=tmp_path / "executions",
                backend=_NeverCalledBackend(),
            )

    def test_missing_extracted_code_raises(self, tmp_path):
        path = _write_gen_artifact(tmp_path, extracted_code=None)
        with pytest.raises(ExecutionIntegrationError, match="extracted_code"):
            execute_generation_artifact(
                path,
                output_root=tmp_path / "executions",
                backend=_NeverCalledBackend(),
            )

    def test_empty_extracted_code_raises(self, tmp_path):
        path = _write_gen_artifact(tmp_path, extracted_code="   ")
        with pytest.raises(ExecutionIntegrationError, match="extracted_code"):
            execute_generation_artifact(
                path,
                output_root=tmp_path / "executions",
                backend=_NeverCalledBackend(),
            )

    def test_missing_benchmark_raises(self, tmp_path):
        path = _write_gen_artifact(tmp_path, benchmark="")
        with pytest.raises(ExecutionIntegrationError, match="benchmark"):
            execute_generation_artifact(
                path,
                output_root=tmp_path / "executions",
                backend=_NeverCalledBackend(),
            )

    def test_missing_task_id_raises(self, tmp_path):
        path = _write_gen_artifact(tmp_path, task_id="")
        with pytest.raises(ExecutionIntegrationError, match="task_id"):
            execute_generation_artifact(
                path,
                output_root=tmp_path / "executions",
                backend=_NeverCalledBackend(),
            )

    def test_task_id_not_found_raises(self, tmp_path):
        path = _write_gen_artifact(tmp_path, task_id="tiny_999")
        with pytest.raises(ExecutionIntegrationError, match="tiny_999"):
            execute_generation_artifact(
                path,
                output_root=tmp_path / "executions",
                backend=_NeverCalledBackend(),
            )

    def test_unreadable_artifact_raises(self, tmp_path):
        bad_path = tmp_path / "does_not_exist.json"
        with pytest.raises(ExecutionIntegrationError):
            execute_generation_artifact(
                bad_path,
                output_root=tmp_path / "executions",
                backend=_NeverCalledBackend(),
            )


# ── 4. docker_used flag ───────────────────────────────────────────────────────

class TestDockerUsedFlag:
    def test_use_docker_true_returns_docker_used_true(self, tmp_path):
        path = _write_gen_artifact(tmp_path)
        summary = execute_generation_artifact(
            path,
            output_root=tmp_path / "executions",
            backend=_SuccessBackend(),
            use_docker=True,
        )
        assert summary["docker_used"] is True
        assert summary["runner_type"] == "docker"

    def test_use_docker_false_returns_docker_used_false(self, tmp_path):
        # execute_locally with trusted correct code from tiny fixture
        path = _write_gen_artifact(
            tmp_path,
            extracted_code="def add(a, b): return a + b",
        )
        summary = execute_generation_artifact(
            path,
            output_root=tmp_path / "executions",
            use_docker=False,
        )
        assert summary["docker_used"] is False
        assert summary["runner_type"] == "local"

    def test_use_docker_false_passes_with_correct_code(self, tmp_path):
        path = _write_gen_artifact(
            tmp_path,
            extracted_code="def add(a, b): return a + b",
        )
        summary = execute_generation_artifact(
            path,
            output_root=tmp_path / "executions",
            use_docker=False,
        )
        assert summary["tests_passed"] is True


# ── 5. execution_performed invariant ─────────────────────────────────────────

class TestExecutionPerformed:
    def test_execution_performed_true(self, tmp_path):
        path = _write_gen_artifact(tmp_path)
        summary = execute_generation_artifact(
            path,
            output_root=tmp_path / "executions",
            backend=_SuccessBackend(),
        )
        assert summary["execution_performed"] is True


# ── 6. No secrets in artifact ─────────────────────────────────────────────────

def _collect_string_values(obj) -> list[str]:
    """Recursively collect all string values from a JSON-decoded object.

    Keys are intentionally excluded — schema field names like 'task_id' are
    allowed; only values must not contain secrets.
    """
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        result = []
        for v in obj.values():
            result.extend(_collect_string_values(v))
        return result
    if isinstance(obj, list):
        result = []
        for item in obj:
            result.extend(_collect_string_values(item))
        return result
    return []


class TestNoSecrets:
    def test_artifact_no_api_key(self, tmp_path):
        gen_path = _write_gen_artifact(tmp_path)
        summary = execute_generation_artifact(
            gen_path,
            output_root=tmp_path / "executions",
            backend=_SuccessBackend(),
        )
        with open(summary["execution_artifact_path"], encoding="utf-8") as f:
            artifact = json.load(f)
        values = _collect_string_values(artifact)
        # Check values for actual secret patterns — not bare "api_key" which
        # can appear in file paths derived from the test function name.
        forbidden = ["DEEPSEEK_API_KEY", "deepseek_api_key", "api_key=", "sk-"]
        for v in values:
            for pattern in forbidden:
                assert pattern not in v, (
                    f"Secret pattern {pattern!r} found in artifact value: {v!r}"
                )

    def test_artifact_no_sk_token(self, tmp_path):
        gen_path = _write_gen_artifact(tmp_path)
        summary = execute_generation_artifact(
            gen_path,
            output_root=tmp_path / "executions",
            backend=_SuccessBackend(),
        )
        with open(summary["execution_artifact_path"], encoding="utf-8") as f:
            content = f.read()
        assert "sk-" not in content

    def test_artifact_no_env_reference(self, tmp_path):
        gen_path = _write_gen_artifact(tmp_path)
        summary = execute_generation_artifact(
            gen_path,
            output_root=tmp_path / "executions",
            backend=_SuccessBackend(),
        )
        with open(summary["execution_artifact_path"], encoding="utf-8") as f:
            content = f.read().lower()
        assert ".env" not in content


# ── 8. timeout_ms forwarding ─────────────────────────────────────────────────

class _CapturingBackend:
    """Records the timeout_ms passed to run_python, succeeds unconditionally."""

    def __init__(self):
        self.last_timeout_ms: int | None = None

    def run_python(self, source_code: str, timeout_ms: int) -> DockerBackendResult:
        self.last_timeout_ms = timeout_ms
        return DockerBackendResult(
            exit_code=0, stdout="", stderr="", timed_out=False, execution_time_ms=5
        )


class TestTimeoutMs:
    def test_default_timeout_ms_is_10000(self, tmp_path):
        path = _write_gen_artifact(tmp_path)
        backend = _CapturingBackend()
        execute_generation_artifact(
            path,
            output_root=tmp_path / "executions",
            backend=backend,
        )
        assert backend.last_timeout_ms == 10000

    def test_custom_timeout_ms_forwarded(self, tmp_path):
        path = _write_gen_artifact(tmp_path)
        backend = _CapturingBackend()
        execute_generation_artifact(
            path,
            output_root=tmp_path / "executions",
            backend=backend,
            timeout_ms=15000,
        )
        assert backend.last_timeout_ms == 15000

    def test_timeout_ms_1000_forwarded(self, tmp_path):
        path = _write_gen_artifact(tmp_path)
        backend = _CapturingBackend()
        execute_generation_artifact(
            path,
            output_root=tmp_path / "executions",
            backend=backend,
            timeout_ms=1000,
        )
        assert backend.last_timeout_ms == 1000

    def test_timeout_ms_in_execution_input(self, tmp_path):
        """timeout_ms must reach ExecutionInput (verified via backend call)."""
        path = _write_gen_artifact(tmp_path)
        backend = _CapturingBackend()
        execute_generation_artifact(
            path,
            output_root=tmp_path / "executions",
            backend=backend,
            timeout_ms=8000,
        )
        assert backend.last_timeout_ms == 8000


# ── 7. No forbidden imports in integration.py ─────────────────────────────────

def _collect_imports(src: str) -> set[str]:
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


class TestNoForbiddenImports:
    @staticmethod
    def _imports() -> set[str]:
        import reliability_harness.runtime.execution.integration as m
        src = open(m.__file__, encoding="utf-8").read()
        return _collect_imports(src)

    def test_no_llm_client_import(self):
        imports = self._imports()
        assert not any("llm_client" in name.lower() or "LLMClient" in name for name in imports)

    def test_no_memory_import(self):
        imports = self._imports()
        assert not any("reliability_harness.memory" in name for name in imports)

    def test_no_retry_import(self):
        imports = self._imports()
        assert not any("retry_controller" in name for name in imports)

    def test_no_closed_loop_runner_import(self):
        imports = self._imports()
        assert not any("closed_loop_runner" in name for name in imports)

    def test_no_core_llm_import(self):
        imports = self._imports()
        assert not any("core.llm" in name for name in imports)
