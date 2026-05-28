"""Benchmark-5B: Minimal observable failure diagnostics.

Derives minimal failure diagnostic signals from generation and execution
artifact fields only.  These are observable diagnostics, NOT a full failure
taxonomy.  Root-cause analysis, reasoning trace inspection, LLM-as-judge,
tool correctness, retry/recovery, and memory-assisted recovery are out of
scope for this module.

Relation to metrics.process
----------------------------
diagnostics.failure is a companion to metrics.process:

  metrics.process.process_failure_stage == "completed"
  -> diagnostics.failure.failure_stage == "none"

diagnostics.failure does not use "completed" — it describes the stage at
which a failure was observed, not a pipeline completion state.

Not implemented (future work):
  - root-cause analysis
  - LLM-as-judge
  - reasoning trace
  - tool correctness
  - retry / recovery
  - memory-assisted recovery
  - full failure taxonomy
"""
from __future__ import annotations

from typing import Any

_DEFINITION = (
    "minimal observable failure diagnostics derived only from "
    "generation/execution summary fields"
)

_KNOWN_ERROR_TYPES = {"assertion_failure", "syntax_error", "runtime_error"}


def compute_minimal_failure_diagnostics_from_sections(
    generation: dict[str, Any],
    execution: dict[str, Any],
    metrics_process: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute minimal observable failure diagnostics from generation and execution sections.

    Parameters
    ----------
    generation:
        generation section dict (expects extraction_status, has_extracted_code)
    execution:
        execution section dict (expects execution_performed, tests_passed,
        error_type, timed_out)
    metrics_process:
        optional process metrics dict (used only as advisory reference;
        no hard semantic dependency)

    Returns
    -------
    dict with minimal observable failure diagnostic fields.
    is_full_failure_taxonomy is always False.
    failure_stage is "unknown" when required fields are missing or invalid.
    """
    if not isinstance(generation, dict) or not isinstance(execution, dict):
        return _unknown_diagnostics()

    extraction_status = generation.get("extraction_status")
    has_extracted_code = generation.get("has_extracted_code")
    execution_performed = execution.get("execution_performed")
    tests_passed = execution.get("tests_passed")
    error_type = execution.get("error_type")
    timed_out = execution.get("timed_out")

    # Guard: generation section must have extraction_status field present
    if "extraction_status" not in generation:
        return _unknown_diagnostics()

    # ── failure_type derivation (priority order) ───────────────────────────────

    # 2. extraction_status present but not "success"
    if extraction_status != "success":
        return _make(
            failure_observed=True,
            failure_stage="extraction",
            failure_type="extraction_failed",
            failure_source="generation.extraction_status",
            timed_out=bool(timed_out) if isinstance(timed_out, bool) else False,
            error_type=error_type,
        )

    # 3. extraction_status == "success" but has_extracted_code is False
    if has_extracted_code is not True:
        return _make(
            failure_observed=True,
            failure_stage="extraction",
            failure_type="no_extracted_code",
            failure_source="generation.has_extracted_code",
            timed_out=bool(timed_out) if isinstance(timed_out, bool) else False,
            error_type=error_type,
        )

    # extraction succeeded — check execution stage

    # 4. execution_performed is not True
    if execution_performed is not True:
        return _make(
            failure_observed=True,
            failure_stage="execution",
            failure_type="execution_not_performed",
            failure_source="execution.execution_performed",
            timed_out=False,
            error_type=error_type,
        )

    # 5. timed_out
    if timed_out is True:
        return _make(
            failure_observed=True,
            failure_stage="execution",
            failure_type="timeout",
            failure_source="execution.timed_out",
            timed_out=True,
            error_type=error_type,
        )

    # 6. known error_type
    if error_type in _KNOWN_ERROR_TYPES:
        return _make(
            failure_observed=True,
            failure_stage="execution",
            failure_type=error_type,
            failure_source="execution.error_type",
            timed_out=False,
            error_type=error_type,
        )

    # 7. tests_passed False with no identifiable error
    if tests_passed is not True:
        return _make(
            failure_observed=True,
            failure_stage="execution",
            failure_type="unknown_execution_error",
            failure_source="execution.tests_passed",
            timed_out=False,
            error_type=error_type,
        )

    # 8. success — no failure observed
    return _make(
        failure_observed=False,
        failure_stage="none",
        failure_type="none",
        failure_source=None,
        timed_out=False,
        error_type=None,
    )


def compute_minimal_failure_diagnostics(summary: dict[str, Any]) -> dict[str, Any]:
    """Compute minimal observable failure diagnostics from a run summary dict.

    Convenience wrapper around compute_minimal_failure_diagnostics_from_sections.

    Parameters
    ----------
    summary:
        A run summary dict containing 'generation', 'execution', and optionally
        'metrics.process' sections.  Missing or non-dict sections are treated as
        empty dicts, which yields failure_stage == "unknown".
    """
    if not isinstance(summary, dict):
        return _unknown_diagnostics()
    generation = summary.get("generation")
    if not isinstance(generation, dict):
        generation = {}
    execution = summary.get("execution")
    if not isinstance(execution, dict):
        execution = {}
    metrics = summary.get("metrics")
    metrics_process = None
    if isinstance(metrics, dict):
        mp = metrics.get("process")
        if isinstance(mp, dict):
            metrics_process = mp
    return compute_minimal_failure_diagnostics_from_sections(
        generation, execution, metrics_process=metrics_process
    )


def _make(
    *,
    failure_observed: bool,
    failure_stage: str,
    failure_type: str,
    failure_source: str | None,
    timed_out: bool,
    error_type: str | None,
) -> dict[str, Any]:
    return {
        "failure_observed": failure_observed,
        "failure_stage": failure_stage,
        "failure_type": failure_type,
        "failure_source": failure_source,
        "timed_out": timed_out,
        "error_type": error_type,
        "is_full_failure_taxonomy": False,
        "definition": _DEFINITION,
    }


def _unknown_diagnostics() -> dict[str, Any]:
    """Return unknown diagnostics when required fields are missing or invalid."""
    return _make(
        failure_observed=False,
        failure_stage="unknown",
        failure_type="unknown",
        failure_source="missing_required_fields",
        timed_out=False,
        error_type=None,
    )
