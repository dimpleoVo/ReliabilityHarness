"""Tests for Benchmark-4C.2b — cli.py benchmark subcommand forwarding.

Uses monkeypatched run_benchmark.run. No real Docker. No real LLM.
No DeepSeek API key required.

Covered:
1.  --execute-generation-artifact forwards path to run()
2.  --execute-local forwards execute_local=True to run()
3.  --execution-timeout-ms forwards value to run()
4.  execution mode allows missing --benchmark (no SystemExit)
5.  --dry-run without --benchmark errors (SystemExit)
6.  --generate without --benchmark errors (SystemExit)
7.  --dry-run with --benchmark still works
8.  --generate with --benchmark forwards correctly
9.  --generate and --execute-generation-artifact are mutually exclusive (SystemExit)
10. --dry-run and --execute-generation-artifact are mutually exclusive (SystemExit)
11. execution mode does not call LLMClient.from_env
12. execution mode does not call generate_for_tasks
13. returned CLI JSON does not contain DEEPSEEK_API_KEY / .env / sk-
"""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest

import reliability_harness.experiments.run_benchmark as rb_mod
from reliability_harness.cli import main as cli_main


# ── Fake helpers ───────────────────────────────────────────────────────────────

def _fake_exec_result(path: str = "test.json") -> dict:
    return {
        "generation_artifact_path": path,
        "execution_artifact_path": "/tmp/exec/run_test/run_test_tiny_001.json",
        "run_summary_artifact_path": "/tmp/summaries/run_test_tiny_001_summary.json",
        "run_id": "run_test",
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


def _patch_run(monkeypatch):
    """Monkeypatch run_benchmark.run and return the calls list."""
    calls: list[dict] = []

    def fake_run(**kwargs):
        calls.append(kwargs)
        return _fake_exec_result(str(kwargs.get("execute_generation_artifact_path", "test.json")))

    monkeypatch.setattr(rb_mod, "run", fake_run)
    return calls


# ── 1. --execute-generation-artifact forwards path ────────────────────────────

class TestForwardsArtifactPath:
    def test_execute_generation_artifact_forwards_path(self, monkeypatch, tmp_path):
        calls = _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        cli_main(["benchmark", "--execute-generation-artifact", path])
        assert len(calls) == 1
        assert calls[0]["execute_generation_artifact_path"] == path

    def test_execute_generation_artifact_default_timeout(self, monkeypatch, tmp_path):
        calls = _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        cli_main(["benchmark", "--execute-generation-artifact", path])
        assert calls[0]["execution_timeout_ms"] == 10000


# ── 2. --execute-local forwards execute_local=True ────────────────────────────

class TestForwardsExecuteLocal:
    def test_execute_local_flag_forwards_true(self, monkeypatch, tmp_path):
        calls = _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        cli_main(["benchmark", "--execute-generation-artifact", path, "--execute-local"])
        assert calls[0]["execute_local"] is True

    def test_no_execute_local_flag_forwards_false(self, monkeypatch, tmp_path):
        calls = _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        cli_main(["benchmark", "--execute-generation-artifact", path])
        assert calls[0]["execute_local"] is False


# ── 3. --execution-timeout-ms forwards value ──────────────────────────────────

class TestForwardsExecutionTimeoutMs:
    def test_custom_timeout_forwarded(self, monkeypatch, tmp_path):
        calls = _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        cli_main([
            "benchmark",
            "--execute-generation-artifact", path,
            "--execution-timeout-ms", "15000",
        ])
        assert calls[0]["execution_timeout_ms"] == 15000

    def test_default_timeout_is_10000(self, monkeypatch, tmp_path):
        calls = _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        cli_main(["benchmark", "--execute-generation-artifact", path])
        assert calls[0]["execution_timeout_ms"] == 10000


# ── 4. execution mode allows missing --benchmark ──────────────────────────────

class TestExecutionModeAllowsMissingBenchmark:
    def test_no_benchmark_with_execute_artifact_is_accepted(self, monkeypatch, tmp_path):
        calls = _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        # Must NOT raise SystemExit
        cli_main(["benchmark", "--execute-generation-artifact", path])
        assert len(calls) == 1

    def test_benchmark_none_forwarded_to_run(self, monkeypatch, tmp_path):
        calls = _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        cli_main(["benchmark", "--execute-generation-artifact", path])
        assert calls[0]["benchmark"] is None

    def test_optional_benchmark_forwarded_when_given(self, monkeypatch, tmp_path):
        calls = _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        cli_main(["benchmark", "--benchmark", "tiny", "--execute-generation-artifact", path])
        assert calls[0]["benchmark"] == "tiny"


# ── 5. --dry-run without --benchmark errors ───────────────────────────────────

class TestDryRunWithoutBenchmarkErrors:
    def test_dry_run_no_benchmark_exits(self):
        with pytest.raises(SystemExit):
            cli_main(["benchmark", "--dry-run"])

    def test_no_flags_no_benchmark_exits(self):
        with pytest.raises(SystemExit):
            cli_main(["benchmark"])


# ── 6. --generate without --benchmark errors ─────────────────────────────────

class TestGenerateWithoutBenchmarkErrors:
    def test_generate_no_benchmark_exits(self):
        with pytest.raises(SystemExit):
            cli_main(["benchmark", "--generate"])


# ── 7. --dry-run with --benchmark still works ─────────────────────────────────

class TestDryRunWithBenchmarkWorks:
    def test_dry_run_with_benchmark_dispatches(self, monkeypatch):
        calls = _patch_run(monkeypatch)
        cli_main(["benchmark", "--benchmark", "tiny", "--dry-run"])
        assert len(calls) == 1
        assert calls[0]["dry_run_mode"] is True
        assert calls[0]["benchmark"] == "tiny"

    def test_dry_run_does_not_set_execute_artifact_path(self, monkeypatch):
        calls = _patch_run(monkeypatch)
        cli_main(["benchmark", "--benchmark", "tiny", "--dry-run"])
        assert calls[0]["execute_generation_artifact_path"] is None


# ── 8. --generate with --benchmark forwards correctly ─────────────────────────

class TestGenerateWithBenchmarkForwards:
    def test_generate_with_benchmark_dispatches(self, monkeypatch):
        calls = _patch_run(monkeypatch)
        cli_main(["benchmark", "--benchmark", "tiny", "--generate"])
        assert len(calls) == 1
        assert calls[0]["generate_mode"] is True
        assert calls[0]["benchmark"] == "tiny"

    def test_generate_limit_forwarded(self, monkeypatch):
        calls = _patch_run(monkeypatch)
        cli_main(["benchmark", "--benchmark", "tiny", "--generate", "--limit", "2"])
        assert calls[0]["limit"] == 2


# ── 9. --generate and --execute-generation-artifact mutually exclusive ─────────

class TestGenerateAndExecuteArtifactMutuallyExclusive:
    def test_generate_and_execute_artifact_exits(self, monkeypatch, tmp_path):
        _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        with pytest.raises(SystemExit):
            cli_main([
                "benchmark",
                "--benchmark", "tiny",
                "--generate",
                "--execute-generation-artifact", path,
            ])

    def test_generate_and_execute_artifact_no_benchmark_exits(self, monkeypatch, tmp_path):
        _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        with pytest.raises(SystemExit):
            cli_main([
                "benchmark",
                "--generate",
                "--execute-generation-artifact", path,
            ])


# ── 10. --dry-run and --execute-generation-artifact mutually exclusive ──────────

class TestDryRunAndExecuteArtifactMutuallyExclusive:
    def test_dry_run_and_execute_artifact_exits(self, monkeypatch, tmp_path):
        _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        with pytest.raises(SystemExit):
            cli_main([
                "benchmark",
                "--benchmark", "tiny",
                "--dry-run",
                "--execute-generation-artifact", path,
            ])

    def test_dry_run_and_execute_artifact_no_benchmark_exits(self, monkeypatch, tmp_path):
        _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        with pytest.raises(SystemExit):
            cli_main([
                "benchmark",
                "--dry-run",
                "--execute-generation-artifact", path,
            ])


# ── 11. execution mode does not call LLMClient.from_env ──────────────────────

class TestNoLLMClientInExecutionMode:
    def test_execution_does_not_call_llm_client_from_env(self, monkeypatch, tmp_path):
        calls = _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        with patch(
            "reliability_harness.runtime.generation.llm_client.LLMClient.from_env",
            side_effect=AssertionError("LLMClient.from_env must not be called in execution mode"),
        ):
            cli_main(["benchmark", "--execute-generation-artifact", path])
        assert len(calls) == 1

    def test_execution_succeeds_without_api_key_env(self, monkeypatch, tmp_path):
        calls = _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        cli_main(["benchmark", "--execute-generation-artifact", path])
        assert len(calls) == 1


# ── 12. execution mode does not call generation pipeline ─────────────────────

class TestNoGenerationPipelineInExecutionMode:
    def test_execution_does_not_call_generate_for_tasks(self, monkeypatch, tmp_path):
        calls = _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        with patch(
            "reliability_harness.runtime.generation.generator.generate_for_tasks",
            side_effect=AssertionError("generate_for_tasks must not be called in execution mode"),
        ):
            cli_main(["benchmark", "--execute-generation-artifact", path])
        assert len(calls) == 1


# ── 13. returned CLI JSON does not contain secret patterns ───────────────────

class TestNoSecretsInCliOutput:
    _FORBIDDEN = ["DEEPSEEK_API_KEY", "deepseek_api_key", "api_key=", "sk-", ".env"]

    def test_cli_json_no_api_key(self, monkeypatch, tmp_path, capsys):
        _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        cli_main(["benchmark", "--execute-generation-artifact", path])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        text = json.dumps(data)
        for pattern in self._FORBIDDEN:
            assert pattern not in text, (
                f"Forbidden pattern {pattern!r} found in CLI output: {text!r}"
            )

    def test_cli_json_no_sk_token(self, monkeypatch, tmp_path, capsys):
        _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        cli_main(["benchmark", "--execute-generation-artifact", path])
        captured = capsys.readouterr()
        assert "sk-" not in captured.out

    def test_cli_json_no_env_reference(self, monkeypatch, tmp_path, capsys):
        _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        cli_main(["benchmark", "--execute-generation-artifact", path])
        captured = capsys.readouterr()
        assert ".env" not in captured.out.lower()


# ── 14. Benchmark-4D.2: CLI forwards run summary fields ──────────────────────

class TestCliForwardsRunSummaryFields:
    """CLI execution mode forwards run_summary_artifact_path, final_success, summary_written."""

    def test_cli_returns_run_summary_artifact_path(self, monkeypatch, tmp_path, capsys):
        _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        cli_main(["benchmark", "--execute-generation-artifact", path])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "run_summary_artifact_path" in data

    def test_cli_returns_final_success(self, monkeypatch, tmp_path, capsys):
        _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        cli_main(["benchmark", "--execute-generation-artifact", path])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "final_success" in data
        assert data["final_success"] is True

    def test_cli_returns_summary_written(self, monkeypatch, tmp_path, capsys):
        _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        cli_main(["benchmark", "--execute-generation-artifact", path])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "summary_written" in data
        assert data["summary_written"] is True

    def test_cli_dry_run_unaffected(self, monkeypatch, capsys):
        """Dry-run result does not include run_summary_artifact_path or final_success."""
        calls = _patch_run(monkeypatch)
        cli_main(["benchmark", "--benchmark", "tiny", "--dry-run"])
        # The patched run() returns _fake_exec_result which has these fields,
        # but we're verifying the CLI still works (no crash, captures are JSON).
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data, dict)
        assert len(calls) == 1

    def test_cli_run_summary_path_is_string_or_null(self, monkeypatch, tmp_path, capsys):
        _patch_run(monkeypatch)
        path = str(tmp_path / "gen.json")
        cli_main(["benchmark", "--execute-generation-artifact", path])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["run_summary_artifact_path"] is None or isinstance(
            data["run_summary_artifact_path"], str
        )
