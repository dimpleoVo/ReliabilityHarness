"""Tests for Benchmark-6B.1 — run_benchmark aggregate summary entrypoint.

Uses monkeypatched aggregate summary helpers. No real file reads. No LLM. No Docker.
No API key required.

Covered:
1.  aggregate mode calls build_aggregate_summary_from_paths
2.  aggregate mode writes aggregate summary artifact
3.  returned JSON includes aggregate_summary_artifact_path
4.  returned JSON includes summary_written true
5.  returned JSON includes counts / rates / distributions
6.  aggregate mode accepts multiple paths
7.  aggregate mode accepts single path
8.  aggregate mode does not require --benchmark
9.  dry-run remains unaffected
10. generate remains unaffected
11. execute-generation-artifact remains unaffected
12. aggregate mode does not call LLM
13. aggregate mode does not call Docker / execution integration
14. aggregate mode rejects --generate + --aggregate-run-summaries
15. aggregate mode rejects --dry-run + --aggregate-run-summaries
16. aggregate mode rejects --execute-generation-artifact + --aggregate-run-summaries
17. missing/invalid paths propagate AggregateSummaryError
18. main() accepts --aggregate-run-summaries p1 p2 without --benchmark
19. --benchmark remains required for dry-run/generate
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

import reliability_harness.experiments.run_benchmark as rb_mod
from reliability_harness.experiments.run_benchmark import run
from reliability_harness.artifacts.aggregate_summary import AggregateSummaryError


# ── Fake helpers ───────────────────────────────────────────────────────────────

_FAKE_ARTIFACT_PATH = "/tmp/aggregate_summaries/aggregate_summary_fake.json"


def _fake_aggregate_summary_dict(paths):
    return {
        "artifact_version": "6A.1",
        "created_at": "2026-01-01T00:00:00+00:00",
        "input": {"run_summary_paths": [str(p) for p in paths]},
        "counts": {
            "total_runs": len(paths),
            "final_success_count": 0,
            "observable_process_success_count": 0,
            "failure_observed_count": 0,
            "timeout_count": 0,
            "runtime_error_count": 0,
        },
        "rates": {
            "final_success_rate": 0.0,
            "observable_process_success_rate": 0.0,
            "failure_observed_rate": 0.0,
            "timeout_rate": 0.0,
            "runtime_error_rate": 0.0,
        },
        "distributions": {
            "failure_stage_distribution": {},
            "failure_type_distribution": {},
        },
        "limitations": [],
    }


def _patch_aggregate_helpers(monkeypatch, tmp_path=None):
    """Patch build_aggregate_summary_from_paths and write_aggregate_summary at module level."""
    build_calls: list = []
    write_calls: list = []
    artifact_path = Path(tmp_path / "agg.json") if tmp_path else Path(_FAKE_ARTIFACT_PATH)

    def fake_build(paths):
        build_calls.append(list(paths))
        return _fake_aggregate_summary_dict(paths)

    def fake_write(summary, output_dir=None):
        write_calls.append(summary)
        if tmp_path:
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
        return artifact_path

    monkeypatch.setattr(
        "reliability_harness.artifacts.aggregate_summary.build_aggregate_summary_from_paths",
        fake_build,
    )
    monkeypatch.setattr(
        "reliability_harness.artifacts.aggregate_summary.write_aggregate_summary",
        fake_write,
    )
    return build_calls, write_calls, artifact_path


def _patch_aggregate_entrypoint(monkeypatch, calls=None):
    """Patch _execute_aggregate_run_summaries_entrypoint directly on rb_mod."""
    if calls is None:
        calls = []

    def fake(paths):
        calls.append(list(paths))
        return {
            "aggregate_summary_artifact_path": _FAKE_ARTIFACT_PATH,
            "summary_written": True,
            "input": {"run_summary_paths": [str(p) for p in paths]},
            "counts": {
                "total_runs": len(paths),
                "final_success_count": 0,
                "observable_process_success_count": 0,
                "failure_observed_count": 0,
                "timeout_count": 0,
                "runtime_error_count": 0,
            },
            "rates": {
                "final_success_rate": 0.0,
                "observable_process_success_rate": 0.0,
                "failure_observed_rate": 0.0,
                "timeout_rate": 0.0,
                "runtime_error_rate": 0.0,
            },
            "distributions": {
                "failure_stage_distribution": {},
                "failure_type_distribution": {},
            },
            "artifact_version": "6A.1",
        }

    monkeypatch.setattr(rb_mod, "_execute_aggregate_run_summaries_entrypoint", fake)
    return calls


# ── 1 & 2. build and write internal calls ─────────────────────────────────────

class TestAggregateBuildAndWrite:
    def test_calls_build_aggregate_summary_from_paths(self, monkeypatch, tmp_path):
        build_calls, _, _ = _patch_aggregate_helpers(monkeypatch, tmp_path)
        paths = ["/tmp/run_a.json", "/tmp/run_b.json"]
        run(aggregate_run_summary_paths=paths)
        assert len(build_calls) == 1
        assert build_calls[0] == paths

    def test_build_receives_all_paths(self, monkeypatch, tmp_path):
        build_calls, _, _ = _patch_aggregate_helpers(monkeypatch, tmp_path)
        paths = ["/tmp/a.json", "/tmp/b.json", "/tmp/c.json"]
        run(aggregate_run_summary_paths=paths)
        assert build_calls[0] == paths

    def test_writes_aggregate_summary_artifact(self, monkeypatch, tmp_path):
        _, write_calls, _ = _patch_aggregate_helpers(monkeypatch, tmp_path)
        paths = ["/tmp/run_a.json"]
        run(aggregate_run_summary_paths=paths)
        assert len(write_calls) == 1

    def test_write_receives_summary_dict(self, monkeypatch, tmp_path):
        _, write_calls, _ = _patch_aggregate_helpers(monkeypatch, tmp_path)
        run(aggregate_run_summary_paths=["/tmp/a.json"])
        assert isinstance(write_calls[0], dict)
        assert "counts" in write_calls[0]


# ── 3, 4, 5. Return value fields ──────────────────────────────────────────────

class TestReturnFields:
    def test_returns_aggregate_summary_artifact_path(self, monkeypatch):
        _patch_aggregate_entrypoint(monkeypatch)
        result = run(aggregate_run_summary_paths=["/tmp/a.json"])
        assert "aggregate_summary_artifact_path" in result

    def test_aggregate_summary_artifact_path_is_string(self, monkeypatch):
        _patch_aggregate_entrypoint(monkeypatch)
        result = run(aggregate_run_summary_paths=["/tmp/a.json"])
        assert isinstance(result["aggregate_summary_artifact_path"], str)

    def test_returns_summary_written_true(self, monkeypatch):
        _patch_aggregate_entrypoint(monkeypatch)
        result = run(aggregate_run_summary_paths=["/tmp/a.json"])
        assert result["summary_written"] is True

    def test_returns_counts(self, monkeypatch):
        _patch_aggregate_entrypoint(monkeypatch)
        result = run(aggregate_run_summary_paths=["/tmp/a.json"])
        assert "counts" in result
        assert isinstance(result["counts"], dict)

    def test_returns_rates(self, monkeypatch):
        _patch_aggregate_entrypoint(monkeypatch)
        result = run(aggregate_run_summary_paths=["/tmp/a.json"])
        assert "rates" in result
        assert isinstance(result["rates"], dict)

    def test_returns_distributions(self, monkeypatch):
        _patch_aggregate_entrypoint(monkeypatch)
        result = run(aggregate_run_summary_paths=["/tmp/a.json"])
        assert "distributions" in result
        assert isinstance(result["distributions"], dict)

    def test_returns_input(self, monkeypatch):
        _patch_aggregate_entrypoint(monkeypatch)
        result = run(aggregate_run_summary_paths=["/tmp/a.json"])
        assert "input" in result
        assert isinstance(result["input"], dict)

    def test_artifact_path_matches_written_path(self, monkeypatch, tmp_path):
        _, _, artifact_path = _patch_aggregate_helpers(monkeypatch, tmp_path)
        result = run(aggregate_run_summary_paths=["/tmp/a.json"])
        assert result["aggregate_summary_artifact_path"] == str(artifact_path)


# ── 6 & 7. Accept multiple/single paths ───────────────────────────────────────

class TestPathAcceptance:
    def test_accepts_multiple_paths(self, monkeypatch):
        calls = _patch_aggregate_entrypoint(monkeypatch)
        paths = ["/tmp/a.json", "/tmp/b.json", "/tmp/c.json"]
        run(aggregate_run_summary_paths=paths)
        assert calls[0] == paths

    def test_accepts_single_path(self, monkeypatch):
        calls = _patch_aggregate_entrypoint(monkeypatch)
        paths = ["/tmp/a.json"]
        run(aggregate_run_summary_paths=paths)
        assert calls[0] == paths

    def test_passes_paths_unchanged(self, monkeypatch):
        calls = _patch_aggregate_entrypoint(monkeypatch)
        paths = ["/data/run_1.json", "/data/run_2.json"]
        run(aggregate_run_summary_paths=paths)
        assert calls[0] == paths


# ── 8. Does not require --benchmark ───────────────────────────────────────────

class TestNoBenchmarkRequired:
    def test_aggregate_mode_does_not_require_benchmark(self, monkeypatch):
        _patch_aggregate_entrypoint(monkeypatch)
        result = run(aggregate_run_summary_paths=["/tmp/a.json"])
        assert isinstance(result, dict)

    def test_aggregate_mode_benchmark_none_is_accepted(self, monkeypatch):
        _patch_aggregate_entrypoint(monkeypatch)
        result = run(benchmark=None, aggregate_run_summary_paths=["/tmp/a.json"])
        assert "aggregate_summary_artifact_path" in result


# ── 9. dry-run remains unaffected ─────────────────────────────────────────────

class TestDryRunUnaffected:
    def test_dry_run_still_works(self):
        result = run("tiny", dry_run_mode=True)
        assert result["benchmark"] == "tiny"
        assert result["status"] == "dry-run skeleton"

    def test_dry_run_does_not_include_aggregate_fields(self):
        result = run("tiny", dry_run_mode=True)
        assert "aggregate_summary_artifact_path" not in result
        assert "summary_written" not in result

    def test_dry_run_does_not_call_aggregate_entrypoint(self, monkeypatch):
        agg_calls = _patch_aggregate_entrypoint(monkeypatch)
        run("tiny", dry_run_mode=True)
        assert len(agg_calls) == 0


# ── 10. generate remains unaffected ───────────────────────────────────────────

class TestGenerateModeUnaffected:
    def test_generate_mode_dispatches_to_execute_generate(self, monkeypatch):
        generate_calls: list = []

        def fake_execute_generate(**kwargs):
            generate_calls.append(kwargs)
            return {"status": "generated", "benchmark": kwargs.get("benchmark"), "num_tasks": 0}

        monkeypatch.setattr(rb_mod, "_execute_generate", fake_execute_generate)
        run("tiny", generate_mode=True)
        assert len(generate_calls) == 1

    def test_generate_mode_does_not_call_aggregate_entrypoint(self, monkeypatch):
        agg_calls = _patch_aggregate_entrypoint(monkeypatch)

        def fake_execute_generate(**kwargs):
            return {"status": "generated", "benchmark": "tiny", "num_tasks": 0}

        monkeypatch.setattr(rb_mod, "_execute_generate", fake_execute_generate)
        run("tiny", generate_mode=True)
        assert len(agg_calls) == 0


# ── 11. execute-generation-artifact remains unaffected ────────────────────────

class TestExecuteGenerationArtifactUnaffected:
    def test_execute_generation_artifact_dispatches(self, monkeypatch, tmp_path):
        execute_calls: list = []

        def fake_execute_gen_artifact(**kwargs):
            execute_calls.append(kwargs)
            return {"generation_artifact_path": kwargs.get("path", ""), "tests_passed": True}

        monkeypatch.setattr(
            rb_mod, "_execute_generation_artifact_entrypoint", fake_execute_gen_artifact
        )
        run(execute_generation_artifact_path=str(tmp_path / "gen.json"))
        assert len(execute_calls) == 1

    def test_execute_generation_artifact_does_not_call_aggregate(self, monkeypatch, tmp_path):
        agg_calls = _patch_aggregate_entrypoint(monkeypatch)

        def fake_execute_gen_artifact(**kwargs):
            return {"generation_artifact_path": kwargs.get("path", ""), "tests_passed": True}

        monkeypatch.setattr(
            rb_mod, "_execute_generation_artifact_entrypoint", fake_execute_gen_artifact
        )
        run(execute_generation_artifact_path=str(tmp_path / "gen.json"))
        assert len(agg_calls) == 0


# ── 12. aggregate mode does not call LLM ──────────────────────────────────────

class TestAggregateModeNoLLM:
    def test_aggregate_mode_does_not_call_llm_client_from_env(self, monkeypatch, tmp_path):
        _patch_aggregate_helpers(monkeypatch, tmp_path)

        with patch(
            "reliability_harness.runtime.generation.llm_client.LLMClient.from_env",
            side_effect=AssertionError(
                "LLMClient.from_env must not be called in aggregate mode"
            ),
        ):
            result = run(aggregate_run_summary_paths=["/tmp/a.json"])

        assert isinstance(result, dict)

    def test_aggregate_mode_succeeds_without_api_key(self, monkeypatch, tmp_path):
        _patch_aggregate_helpers(monkeypatch, tmp_path)
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        result = run(aggregate_run_summary_paths=["/tmp/a.json"])
        assert isinstance(result, dict)


# ── 13. aggregate mode does not call Docker / execution integration ────────────

class TestAggregateModeNoDocker:
    def test_aggregate_mode_does_not_call_execute_generation_artifact(
        self, monkeypatch, tmp_path
    ):
        _patch_aggregate_helpers(monkeypatch, tmp_path)

        with patch(
            "reliability_harness.runtime.execution.integration.execute_generation_artifact",
            side_effect=AssertionError(
                "execute_generation_artifact must not be called in aggregate mode"
            ),
        ):
            result = run(aggregate_run_summary_paths=["/tmp/a.json"])

        assert isinstance(result, dict)


# ── 14, 15, 16. Mutual exclusion ──────────────────────────────────────────────

class TestMutualExclusion:
    def test_generate_and_aggregate_raises_value_error(self):
        with pytest.raises(ValueError, match="mutually exclusive"):
            run(
                benchmark="tiny",
                generate_mode=True,
                aggregate_run_summary_paths=["/tmp/a.json"],
            )

    def test_generate_and_aggregate_error_mentions_both(self):
        with pytest.raises(ValueError) as exc_info:
            run(
                benchmark="tiny",
                generate_mode=True,
                aggregate_run_summary_paths=["/tmp/a.json"],
            )
        msg = str(exc_info.value)
        assert "--generate" in msg
        assert "--aggregate-run-summaries" in msg

    def test_dry_run_and_aggregate_raises_value_error(self):
        with pytest.raises(ValueError, match="mutually exclusive"):
            run(
                benchmark="tiny",
                dry_run_mode=True,
                aggregate_run_summary_paths=["/tmp/a.json"],
            )

    def test_dry_run_and_aggregate_error_mentions_both(self):
        with pytest.raises(ValueError) as exc_info:
            run(
                benchmark="tiny",
                dry_run_mode=True,
                aggregate_run_summary_paths=["/tmp/a.json"],
            )
        msg = str(exc_info.value)
        assert "--dry-run" in msg
        assert "--aggregate-run-summaries" in msg

    def test_execute_generation_artifact_and_aggregate_raises_value_error(self, tmp_path):
        with pytest.raises(ValueError, match="mutually exclusive"):
            run(
                execute_generation_artifact_path=str(tmp_path / "gen.json"),
                aggregate_run_summary_paths=["/tmp/a.json"],
            )

    def test_execute_generation_artifact_and_aggregate_error_mentions_both(self, tmp_path):
        with pytest.raises(ValueError) as exc_info:
            run(
                execute_generation_artifact_path=str(tmp_path / "gen.json"),
                aggregate_run_summary_paths=["/tmp/a.json"],
            )
        msg = str(exc_info.value)
        assert "--execute-generation-artifact" in msg
        assert "--aggregate-run-summaries" in msg

    def test_all_four_modes_raises_value_error(self, tmp_path):
        with pytest.raises(ValueError, match="mutually exclusive"):
            run(
                benchmark="tiny",
                dry_run_mode=True,
                generate_mode=True,
                execute_generation_artifact_path=str(tmp_path / "gen.json"),
                aggregate_run_summary_paths=["/tmp/a.json"],
            )


# ── 17. Missing/invalid paths propagate AggregateSummaryError ─────────────────

class TestInvalidPaths:
    def _patch_write_only(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "reliability_harness.artifacts.aggregate_summary.write_aggregate_summary",
            lambda s, output_dir=None: tmp_path / "x.json",
        )

    def test_missing_path_raises_aggregate_summary_error(self, monkeypatch, tmp_path):
        self._patch_write_only(monkeypatch, tmp_path)

        def fake_build_raises(paths):
            raise AggregateSummaryError(f"Artifact file not found: {paths[0]}")

        monkeypatch.setattr(
            "reliability_harness.artifacts.aggregate_summary.build_aggregate_summary_from_paths",
            fake_build_raises,
        )
        with pytest.raises(AggregateSummaryError):
            run(aggregate_run_summary_paths=["/nonexistent/path.json"])

    def test_invalid_json_path_raises_aggregate_summary_error(self, monkeypatch, tmp_path):
        self._patch_write_only(monkeypatch, tmp_path)

        def fake_build_raises(paths):
            raise AggregateSummaryError(f"Artifact file is not valid JSON: {paths[0]}")

        monkeypatch.setattr(
            "reliability_harness.artifacts.aggregate_summary.build_aggregate_summary_from_paths",
            fake_build_raises,
        )
        with pytest.raises(AggregateSummaryError):
            run(aggregate_run_summary_paths=["/tmp/not_json.txt"])

    def test_error_message_contains_path(self, monkeypatch, tmp_path):
        self._patch_write_only(monkeypatch, tmp_path)
        path = "/nonexistent/run_summary.json"

        def fake_build_raises(paths):
            raise AggregateSummaryError(f"Artifact file not found: {paths[0]}")

        monkeypatch.setattr(
            "reliability_harness.artifacts.aggregate_summary.build_aggregate_summary_from_paths",
            fake_build_raises,
        )
        with pytest.raises(AggregateSummaryError, match=path):
            run(aggregate_run_summary_paths=[path])


# ── 18. main() accepts --aggregate-run-summaries without --benchmark ───────────

class TestMainArgvParsing:
    def test_main_aggregate_without_benchmark_accepted(self, monkeypatch, capsys):
        calls = _patch_aggregate_entrypoint(monkeypatch)
        from reliability_harness.experiments.run_benchmark import main
        main(["--aggregate-run-summaries", "/tmp/a.json", "/tmp/b.json"])
        assert len(calls) == 1
        assert calls[0] == ["/tmp/a.json", "/tmp/b.json"]

    def test_main_aggregate_single_path(self, monkeypatch, capsys):
        calls = _patch_aggregate_entrypoint(monkeypatch)
        from reliability_harness.experiments.run_benchmark import main
        main(["--aggregate-run-summaries", "/tmp/a.json"])
        assert len(calls) == 1
        assert calls[0] == ["/tmp/a.json"]

    def test_main_aggregate_output_includes_artifact_path(self, monkeypatch, capsys):
        _patch_aggregate_entrypoint(monkeypatch)
        from reliability_harness.experiments.run_benchmark import main
        main(["--aggregate-run-summaries", "/tmp/a.json"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "aggregate_summary_artifact_path" in data

    def test_main_aggregate_output_includes_counts(self, monkeypatch, capsys):
        _patch_aggregate_entrypoint(monkeypatch)
        from reliability_harness.experiments.run_benchmark import main
        main(["--aggregate-run-summaries", "/tmp/a.json"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "counts" in data
        assert "rates" in data
        assert "distributions" in data

    def test_main_generate_plus_aggregate_exits(self):
        from reliability_harness.experiments.run_benchmark import main
        with pytest.raises(SystemExit):
            main([
                "--benchmark", "tiny",
                "--generate",
                "--aggregate-run-summaries", "/tmp/a.json",
            ])

    def test_main_dry_run_plus_aggregate_exits(self):
        from reliability_harness.experiments.run_benchmark import main
        with pytest.raises(SystemExit):
            main([
                "--benchmark", "tiny",
                "--dry-run",
                "--aggregate-run-summaries", "/tmp/a.json",
            ])

    def test_main_execute_artifact_plus_aggregate_exits(self, tmp_path):
        from reliability_harness.experiments.run_benchmark import main
        with pytest.raises(SystemExit):
            main([
                "--execute-generation-artifact", str(tmp_path / "gen.json"),
                "--aggregate-run-summaries", "/tmp/a.json",
            ])


# ── 19. --benchmark remains required for dry-run/generate ─────────────────────

class TestBenchmarkStillRequired:
    def test_dry_run_without_benchmark_exits(self):
        from reliability_harness.experiments.run_benchmark import main
        with pytest.raises(SystemExit):
            main(["--dry-run"])

    def test_generate_without_benchmark_exits(self):
        from reliability_harness.experiments.run_benchmark import main
        with pytest.raises(SystemExit):
            main(["--generate"])

    def test_no_mode_no_benchmark_exits(self):
        from reliability_harness.experiments.run_benchmark import main
        with pytest.raises(SystemExit):
            main([])

    def test_dry_run_with_benchmark_works(self, capsys):
        from reliability_harness.experiments.run_benchmark import main
        main(["--benchmark", "tiny", "--dry-run"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["status"] == "dry-run skeleton"

    def test_aggregate_without_benchmark_does_not_exit(self, monkeypatch):
        _patch_aggregate_entrypoint(monkeypatch)
        from reliability_harness.experiments.run_benchmark import main
        main(["--aggregate-run-summaries", "/tmp/a.json"])
