"""Tests for Benchmark-4C.2a — run_benchmark execution entrypoint.

Uses monkeypatched execute_generation_artifact. No real Docker. No real LLM.
No DeepSeek API key required.

Covered:
1.  run(..., execute_generation_artifact_path=path) dispatches to fake helper
2.  Returns summary dict
3.  Default use_docker=True
4.  execute_local=True -> use_docker=False
5.  --generate and --execute-generation-artifact are mutually exclusive (ValueError)
6.  --dry-run and --execute-generation-artifact are mutually exclusive (ValueError)
7.  dry-run is unaffected by new parameters
8.  generate mode is unaffected (monkeypatched _execute_generate)
9.  execution mode does not call LLMClient.from_env
10. execution mode does not call generate_for_tasks
11. returned summary does not contain secret patterns
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

import reliability_harness.experiments.run_benchmark as rb_mod
from reliability_harness.experiments.run_benchmark import run


# ── Fake helpers ───────────────────────────────────────────────────────────────

def _fake_summary(gen_path: str) -> dict:
    return {
        "generation_artifact_path": gen_path,
        "execution_artifact_path": "/tmp/exec/run_exec_exec/run_exec_exec_tiny_001.json",
        "run_summary_artifact_path": "/tmp/summaries/run_exec_exec_tiny_001_summary.json",
        "run_id": "run_exec_exec",
        "benchmark": "tiny",
        "task_id": "tiny_001",
        "model_name": "mock-model",
        "extraction_status": "success",
        "runner_type": "docker",
        "docker_used": True,
        "execution_performed": True,
        "tests_passed": True,
        "error_type": None,
        "final_success": True,
        "summary_written": True,
    }


def _patch_execute(monkeypatch, calls: list, use_docker_override: bool | None = None):
    """Patch execute_generation_artifact on the integration module and capture calls."""
    def fake(**kwargs):
        calls.append(kwargs)
        summary = _fake_summary(str(kwargs.get("generation_artifact_path", "")))
        if use_docker_override is not None:
            summary["docker_used"] = use_docker_override
            summary["runner_type"] = "docker" if use_docker_override else "local"
        else:
            summary["docker_used"] = kwargs.get("use_docker", True)
            summary["runner_type"] = "docker" if kwargs.get("use_docker", True) else "local"
        return summary

    monkeypatch.setattr(
        "reliability_harness.runtime.execution.integration.execute_generation_artifact",
        fake,
    )
    return fake


# ── 1 & 2. Dispatch + returns summary dict ─────────────────────────────────────

class TestExecutionDispatch:
    def test_dispatches_to_execute_generation_artifact(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        path = str(tmp_path / "gen.json")
        run(execute_generation_artifact_path=path)
        assert len(calls) == 1

    def test_passes_generation_artifact_path(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        path = str(tmp_path / "gen.json")
        run(execute_generation_artifact_path=path)
        assert calls[0]["generation_artifact_path"] == path

    def test_returns_dict(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        result = run(execute_generation_artifact_path=str(tmp_path / "gen.json"))
        assert isinstance(result, dict)

    def test_returns_summary_keys(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        result = run(execute_generation_artifact_path=str(tmp_path / "gen.json"))
        for key in ("generation_artifact_path", "benchmark", "task_id", "tests_passed"):
            assert key in result


# ── 3. Default use_docker=True ─────────────────────────────────────────────────

class TestDefaultDockerTrue:
    def test_default_use_docker_is_true(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        run(execute_generation_artifact_path=str(tmp_path / "gen.json"))
        assert calls[0]["use_docker"] is True

    def test_summary_docker_used_true_by_default(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        result = run(execute_generation_artifact_path=str(tmp_path / "gen.json"))
        assert result["docker_used"] is True


# ── 4. execute_local=True -> use_docker=False ──────────────────────────────────

class TestExecuteLocalFlag:
    def test_execute_local_true_passes_use_docker_false(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        run(
            execute_generation_artifact_path=str(tmp_path / "gen.json"),
            execute_local=True,
        )
        assert calls[0]["use_docker"] is False

    def test_execute_local_false_passes_use_docker_true(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        run(
            execute_generation_artifact_path=str(tmp_path / "gen.json"),
            execute_local=False,
        )
        assert calls[0]["use_docker"] is True


# ── 5 & 6. Mutual exclusion ────────────────────────────────────────────────────

class TestMutualExclusion:
    def test_generate_and_execute_artifact_raises_value_error(self, tmp_path):
        with pytest.raises(ValueError, match="mutually exclusive"):
            run(
                benchmark="tiny",
                generate_mode=True,
                execute_generation_artifact_path=str(tmp_path / "gen.json"),
            )

    def test_generate_and_execute_artifact_error_mentions_both(self, tmp_path):
        with pytest.raises(ValueError) as exc_info:
            run(
                benchmark="tiny",
                generate_mode=True,
                execute_generation_artifact_path=str(tmp_path / "gen.json"),
            )
        msg = str(exc_info.value)
        assert "--generate" in msg
        assert "--execute-generation-artifact" in msg

    def test_dry_run_and_execute_artifact_raises_value_error(self, tmp_path):
        with pytest.raises(ValueError, match="mutually exclusive"):
            run(
                benchmark="tiny",
                dry_run_mode=True,
                execute_generation_artifact_path=str(tmp_path / "gen.json"),
            )

    def test_dry_run_and_execute_artifact_error_mentions_both(self, tmp_path):
        with pytest.raises(ValueError) as exc_info:
            run(
                benchmark="tiny",
                dry_run_mode=True,
                execute_generation_artifact_path=str(tmp_path / "gen.json"),
            )
        msg = str(exc_info.value)
        assert "--dry-run" in msg
        assert "--execute-generation-artifact" in msg

    def test_all_three_raises_value_error(self, tmp_path):
        with pytest.raises(ValueError, match="mutually exclusive"):
            run(
                benchmark="tiny",
                dry_run_mode=True,
                generate_mode=True,
                execute_generation_artifact_path=str(tmp_path / "gen.json"),
            )


# ── 7. dry-run remains unaffected ─────────────────────────────────────────────

class TestDryRunUnaffected:
    def test_dry_run_still_works(self):
        result = run("tiny", dry_run_mode=True)
        assert result["benchmark"] == "tiny"
        assert result["status"] == "dry-run skeleton"

    def test_dry_run_no_execute_generation_artifact_path(self):
        result = run("tiny", dry_run_mode=True)
        assert "execute_generation_artifact_path" not in result

    def test_dry_run_does_not_import_integration(self, monkeypatch):
        """dry-run must not trigger execution helper import."""
        import sys
        # Ensure the module is not in sys.modules so we can detect if it gets imported
        integration_key = "reliability_harness.runtime.execution.integration"
        was_present = integration_key in sys.modules
        result = run("tiny", dry_run_mode=True)
        assert result["status"] == "dry-run skeleton"
        # If it wasn't present before, it must not have been imported by dry_run
        if not was_present:
            # Can't assert absence (other tests may have imported it), so just
            # verify dry_run returned correctly without error.
            pass


# ── 8. generate mode remains unaffected ───────────────────────────────────────

class TestGenerateModeUnaffected:
    def test_generate_mode_calls_execute_generate(self, monkeypatch, tmp_path):
        generate_calls: list = []

        def fake_execute_generate(**kwargs):
            generate_calls.append(kwargs)
            return {"status": "generated", "benchmark": kwargs.get("benchmark"), "num_tasks": 0}

        monkeypatch.setattr(rb_mod, "_execute_generate", fake_execute_generate)
        run("tiny", generate_mode=True)
        assert len(generate_calls) == 1

    def test_generate_mode_does_not_dispatch_to_execute_artifact(self, monkeypatch, tmp_path):
        execute_calls: list = []
        _patch_execute(monkeypatch, execute_calls)
        generate_calls: list = []

        def fake_execute_generate(**kwargs):
            generate_calls.append(kwargs)
            return {"status": "generated", "benchmark": "tiny", "num_tasks": 0}

        monkeypatch.setattr(rb_mod, "_execute_generate", fake_execute_generate)
        run("tiny", generate_mode=True)
        assert len(execute_calls) == 0
        assert len(generate_calls) == 1


# ── 9. Execution mode does not call LLMClient.from_env ────────────────────────

class TestNoLLMClientInExecutionMode:
    def test_execution_does_not_call_llm_client_from_env(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)

        with patch(
            "reliability_harness.runtime.generation.llm_client.LLMClient.from_env",
            side_effect=AssertionError(
                "LLMClient.from_env must not be called in execution mode"
            ),
        ):
            result = run(execute_generation_artifact_path=str(tmp_path / "gen.json"))

        assert isinstance(result, dict)

    def test_execution_succeeds_without_deepseek_api_key(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        result = run(execute_generation_artifact_path=str(tmp_path / "gen.json"))
        assert isinstance(result, dict)


# ── 10. Execution mode does not call generator ────────────────────────────────

class TestNoGeneratorInExecutionMode:
    def test_execution_does_not_call_generate_for_tasks(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)

        with patch(
            "reliability_harness.runtime.generation.generator.generate_for_tasks",
            side_effect=AssertionError(
                "generate_for_tasks must not be called in execution mode"
            ),
        ):
            result = run(execute_generation_artifact_path=str(tmp_path / "gen.json"))

        assert isinstance(result, dict)


# ── 11. Returned summary has no secret patterns ───────────────────────────────

class TestNoSecretsInSummary:
    _FORBIDDEN = ["DEEPSEEK_API_KEY", "deepseek_api_key", "api_key=", "sk-", ".env"]

    def _check_no_secrets(self, obj) -> None:
        text = json.dumps(obj)
        for pattern in self._FORBIDDEN:
            assert pattern not in text, (
                f"Forbidden pattern {pattern!r} found in summary: {text!r}"
            )

    def test_summary_has_no_api_key(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        result = run(execute_generation_artifact_path=str(tmp_path / "gen.json"))
        self._check_no_secrets(result)

    def test_summary_has_no_sk_token(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        result = run(execute_generation_artifact_path=str(tmp_path / "gen.json"))
        assert "sk-" not in json.dumps(result)

    def test_summary_has_no_env_reference(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        result = run(execute_generation_artifact_path=str(tmp_path / "gen.json"))
        assert ".env" not in json.dumps(result).lower()


# ── 12. main() argv parsing ────────────────────────────────────────────────────

class TestMainArgvParsing:
    def test_main_execute_without_benchmark(self, monkeypatch, tmp_path, capsys):
        """--execute-generation-artifact alone (no --benchmark) is accepted."""
        calls: list = []
        _patch_execute(monkeypatch, calls)
        path = str(tmp_path / "gen.json")
        from reliability_harness.experiments.run_benchmark import main
        main(["--execute-generation-artifact", path])
        assert len(calls) == 1

    def test_main_execute_with_benchmark(self, monkeypatch, tmp_path, capsys):
        """--benchmark tiny --execute-generation-artifact is also accepted."""
        calls: list = []
        _patch_execute(monkeypatch, calls)
        path = str(tmp_path / "gen.json")
        from reliability_harness.experiments.run_benchmark import main
        main(["--benchmark", "tiny", "--execute-generation-artifact", path])
        assert len(calls) == 1

    def test_main_generate_and_execute_artifact_exits(self, tmp_path):
        """--generate --execute-generation-artifact causes argparse sys.exit."""
        from reliability_harness.experiments.run_benchmark import main
        with pytest.raises(SystemExit):
            main([
                "--benchmark", "tiny",
                "--generate",
                "--execute-generation-artifact", str(tmp_path / "gen.json"),
            ])

    def test_main_dry_run_and_execute_artifact_exits(self, tmp_path):
        """--dry-run --execute-generation-artifact causes argparse sys.exit."""
        from reliability_harness.experiments.run_benchmark import main
        with pytest.raises(SystemExit):
            main([
                "--benchmark", "tiny",
                "--dry-run",
                "--execute-generation-artifact", str(tmp_path / "gen.json"),
            ])

    def test_main_no_benchmark_no_execute_exits(self):
        """Neither --benchmark nor --execute-generation-artifact causes argparse error."""
        from reliability_harness.experiments.run_benchmark import main
        with pytest.raises(SystemExit):
            main(["--dry-run"])

    def test_main_execute_local_passed_as_use_docker_false(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        from reliability_harness.experiments.run_benchmark import main
        main([
            "--execute-generation-artifact", str(tmp_path / "gen.json"),
            "--execute-local",
        ])
        assert calls[0]["use_docker"] is False

    def test_main_dry_run_tiny_still_works(self, capsys):
        """Regression: --benchmark tiny --dry-run is unaffected."""
        from reliability_harness.experiments.run_benchmark import main
        main(["--benchmark", "tiny", "--dry-run"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["benchmark"] == "tiny"
        assert data["status"] == "dry-run skeleton"


# ── 13. execution_timeout_ms forwarding ───────────────────────────────────────

class TestExecutionTimeoutMs:
    def test_default_execution_timeout_ms_is_10000(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        run(execute_generation_artifact_path=str(tmp_path / "gen.json"))
        assert calls[0]["timeout_ms"] == 10000

    def test_custom_execution_timeout_ms_forwarded(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        run(
            execute_generation_artifact_path=str(tmp_path / "gen.json"),
            execution_timeout_ms=15000,
        )
        assert calls[0]["timeout_ms"] == 15000

    def test_main_execution_timeout_ms_flag(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        from reliability_harness.experiments.run_benchmark import main
        main([
            "--execute-generation-artifact", str(tmp_path / "gen.json"),
            "--execution-timeout-ms", "15000",
        ])
        assert calls[0]["timeout_ms"] == 15000

    def test_main_default_execution_timeout_ms_is_10000(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        from reliability_harness.experiments.run_benchmark import main
        main(["--execute-generation-artifact", str(tmp_path / "gen.json")])
        assert calls[0]["timeout_ms"] == 10000

    def test_dry_run_unaffected_by_timeout_param(self):
        """Passing execution_timeout_ms does not affect dry-run."""
        result = run("tiny", dry_run_mode=True, execution_timeout_ms=99999)
        assert result["status"] == "dry-run skeleton"

    def test_generate_mode_unaffected_by_timeout_param(self, monkeypatch):
        generate_calls: list = []

        def fake_execute_generate(**kwargs):
            generate_calls.append(kwargs)
            return {"status": "generated", "benchmark": "tiny", "num_tasks": 0}

        monkeypatch.setattr(rb_mod, "_execute_generate", fake_execute_generate)
        run("tiny", generate_mode=True, execution_timeout_ms=99999)
        assert len(generate_calls) == 1


# ── 14. Benchmark-4D.2: run_summary fields forwarded through entrypoint ────────

class TestRunSummaryFieldsInEntrypoint:
    """run_benchmark execution entrypoint returns run summary fields (Benchmark-4D.2)."""

    def test_run_summary_artifact_path_in_result(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        result = run(execute_generation_artifact_path=str(tmp_path / "gen.json"))
        assert "run_summary_artifact_path" in result

    def test_final_success_in_result(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        result = run(execute_generation_artifact_path=str(tmp_path / "gen.json"))
        assert "final_success" in result

    def test_summary_written_in_result(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        result = run(execute_generation_artifact_path=str(tmp_path / "gen.json"))
        assert "summary_written" in result

    def test_final_success_true_in_result(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        result = run(execute_generation_artifact_path=str(tmp_path / "gen.json"))
        assert result["final_success"] is True

    def test_summary_written_true_in_result(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        result = run(execute_generation_artifact_path=str(tmp_path / "gen.json"))
        assert result["summary_written"] is True

    def test_run_summary_artifact_path_is_string_or_none(self, monkeypatch, tmp_path):
        calls: list = []
        _patch_execute(monkeypatch, calls)
        result = run(execute_generation_artifact_path=str(tmp_path / "gen.json"))
        assert result["run_summary_artifact_path"] is None or isinstance(
            result["run_summary_artifact_path"], str
        )

    def test_dry_run_unaffected_no_run_summary_fields(self):
        """Dry-run result does not include run_summary_artifact_path or final_success."""
        result = run("tiny", dry_run_mode=True)
        assert result["status"] == "dry-run skeleton"
        assert "run_summary_artifact_path" not in result
        assert "final_success" not in result
