"""Benchmark-6A: Aggregate summary over run summaries.

Aggregates multiple per-task run summary artifacts into a single machine-readable
aggregate summary for paper tables and experiment statistics.

Design
------
- Reads only the minimal observable fields from each run summary:
    success.final_success
    metrics.process.observable_process_success
    metrics.process.timeout_observed
    metrics.process.runtime_error_observed
    diagnostics.failure.failure_observed
    diagnostics.failure.failure_stage
    diagnostics.failure.failure_type
- Does NOT copy prompt, raw_response, extracted_code, candidate_code, stdout, stderr.
- Does NOT execute code, call LLM, or use Docker.
- rates are aggregate statistics, NOT reliability scores or process correctness scores.

Not in scope (Benchmark-6A boundaries):
  - batch execution or code generation
  - retry / recovery metrics
  - memory metrics
  - reasoning consistency, tool correctness
  - LLM-as-judge, full failure taxonomy
  - report generation
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reliability_harness.utils.paths import ARTIFACTS_ROOT

_ARTIFACT_VERSION = "6A.1"
_AGGREGATE_SUMMARIES_ROOT = ARTIFACTS_ROOT / "aggregate_summaries"

_REQUIRED_PATHS: tuple[tuple[str, ...], ...] = (
    ("success", "final_success"),
    ("metrics", "process", "observable_process_success"),
    ("metrics", "process", "timeout_observed"),
    ("metrics", "process", "runtime_error_observed"),
    ("diagnostics", "failure", "failure_observed"),
    ("diagnostics", "failure", "failure_stage"),
    ("diagnostics", "failure", "failure_type"),
)


class AggregateSummaryError(ValueError):
    """Raised when aggregate summary cannot be built due to missing or invalid input."""


def load_json(path: str | Path) -> dict[str, Any]:
    """Load a JSON artifact from disk. Raises AggregateSummaryError on failure."""
    p = Path(path)
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise AggregateSummaryError(f"Artifact file not found: {p}") from exc
    except json.JSONDecodeError as exc:
        raise AggregateSummaryError(f"Artifact file is not valid JSON: {p}") from exc


def _get_nested(d: Any, *keys: str) -> Any:
    """Navigate nested dict by key path. Returns the value or raises KeyError."""
    for key in keys:
        if not isinstance(d, dict):
            raise KeyError(f"Expected dict at key path up to {key!r}, got {type(d).__name__}")
        d = d[key]
    return d


def _validate_and_extract(summary: Any, index: int) -> dict[str, Any]:
    """Extract required fields from one run summary. Raises AggregateSummaryError if missing."""
    if not isinstance(summary, dict):
        raise AggregateSummaryError(
            f"Run summary at index {index} is not a dict (got {type(summary).__name__})"
        )
    extracted: dict[str, Any] = {}
    for path in _REQUIRED_PATHS:
        dotted = ".".join(path)
        try:
            extracted[dotted] = _get_nested(summary, *path)
        except (KeyError, TypeError) as exc:
            raise AggregateSummaryError(
                f"Run summary at index {index} is missing required field '{dotted}': {exc}"
            ) from exc
    return extracted


def build_aggregate_summary(
    run_summaries: list[dict[str, Any]],
    *,
    run_summary_paths: list[str | Path] | None = None,
) -> dict[str, Any]:
    """Build an aggregate summary from a list of run summary dicts.

    Parameters
    ----------
    run_summaries:
        List of run summary dicts (each produced by build_run_summary).
        May be empty — returns zero counts and 0.0 rates.
    run_summary_paths:
        Optional list of source file paths, stored in input.run_summary_paths.
        Length must match run_summaries when provided.

    Returns
    -------
    dict
        Aggregate summary with artifact_version "6A.1".

    Raises
    ------
    AggregateSummaryError
        When run_summaries is not a list, or a summary is missing required fields.
    """
    if not isinstance(run_summaries, list):
        raise AggregateSummaryError(
            f"run_summaries must be a list, got {type(run_summaries).__name__}"
        )

    paths_as_str: list[str] = (
        [str(p) for p in run_summary_paths]
        if run_summary_paths is not None
        else []
    )

    total = len(run_summaries)

    # ── counters ──────────────────────────────────────────────────────────────
    final_success_count = 0
    obs_proc_success_count = 0
    failure_observed_count = 0
    timeout_count = 0
    runtime_error_count = 0
    failure_stage_counter: Counter[str] = Counter()
    failure_type_counter: Counter[str] = Counter()

    for i, summary in enumerate(run_summaries):
        fields = _validate_and_extract(summary, i)

        if fields["success.final_success"] is True:
            final_success_count += 1
        if fields["metrics.process.observable_process_success"] is True:
            obs_proc_success_count += 1
        if fields["metrics.process.timeout_observed"] is True:
            timeout_count += 1
        if fields["metrics.process.runtime_error_observed"] is True:
            runtime_error_count += 1
        if fields["diagnostics.failure.failure_observed"] is True:
            failure_observed_count += 1

        failure_stage_counter[str(fields["diagnostics.failure.failure_stage"])] += 1
        failure_type_counter[str(fields["diagnostics.failure.failure_type"])] += 1

    # ── rates (no divide-by-zero) ─────────────────────────────────────────────
    def _rate(count: int) -> float:
        return round(count / total, 6) if total > 0 else 0.0

    return {
        "artifact_version": _ARTIFACT_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "run_summary_paths": paths_as_str,
        },
        "counts": {
            "total_runs": total,
            "final_success_count": final_success_count,
            "observable_process_success_count": obs_proc_success_count,
            "failure_observed_count": failure_observed_count,
            "timeout_count": timeout_count,
            "runtime_error_count": runtime_error_count,
        },
        "rates": {
            "final_success_rate": _rate(final_success_count),
            "observable_process_success_rate": _rate(obs_proc_success_count),
            "failure_observed_rate": _rate(failure_observed_count),
            "timeout_rate": _rate(timeout_count),
            "runtime_error_rate": _rate(runtime_error_count),
        },
        "distributions": {
            "failure_stage_distribution": dict(failure_stage_counter),
            "failure_type_distribution": dict(failure_type_counter),
        },
        "limitations": [
            (
                "final_success_rate is the fraction of runs where final execution succeeded; "
                "it is NOT a full reliability score"
            ),
            (
                "observable_process_success_rate is based only on minimal observable artifact "
                "fields (Benchmark-5A); it is NOT full process correctness"
            ),
            (
                "aggregate summary does not include reasoning consistency, tool correctness, "
                "retry/recovery, memory metrics, LLM-as-judge, or full failure taxonomy"
            ),
            (
                "aggregate summary does not execute code, call LLM, or use Docker; "
                "it reads only pre-computed run summary artifact fields"
            ),
        ],
    }


def write_aggregate_summary(
    summary: dict[str, Any],
    output_dir: Path | None = None,
) -> Path:
    """Write an aggregate summary dict to disk and return the path.

    Default output directory: outputs/artifacts/aggregate_summaries/
    Filename pattern: aggregate_summary_{YYYYMMDD_HHMMSS_ffffff}.json
    """
    if output_dir is None:
        output_dir = _AGGREGATE_SUMMARIES_ROOT

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    path = output_dir / f"aggregate_summary_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    return path


def build_aggregate_summary_from_paths(
    paths: list[str | Path],
) -> dict[str, Any]:
    """Convenience wrapper: load run summaries from disk and build an aggregate summary.

    Parameters
    ----------
    paths:
        List of filesystem paths to run summary JSON files.

    Raises
    ------
    AggregateSummaryError
        When any file is unreadable or required fields are missing.
    """
    summaries = [load_json(p) for p in paths]
    return build_aggregate_summary(summaries, run_summary_paths=paths)
