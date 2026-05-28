"""Benchmark-5A: Minimal observable process metrics.

Derives minimal process pipeline signals from generation and execution artifact
fields only.  These are observable process signals, NOT full process reliability
metrics.  Full process reliability requires reasoning consistency, tool
correctness, retry/recovery analysis, memory-assisted recovery, and
LLM-as-judge evaluation — none of which are implemented here.

Relation to final_success
--------------------------
observable_process_success may currently align with final_success in simple
single-attempt code-generation tasks.  They are semantically different:

  final_success          — final execution success proxy
                           (extraction_status == success AND execution_performed
                            AND tests_passed)

  observable_process_success — minimal observable pipeline success signal
                           (generation completed → extraction succeeded →
                            execution attempted → execution completed →
                            execution success)

observable_process_success is NOT a replacement for future reasoning/tool/
retry/memory metrics.  is_full_process_reliability_metric is always False.

Not implemented (future work):
  - reasoning consistency
  - tool correctness
  - retry / recovery
  - memory-assisted recovery
  - LLM-as-judge
  - full failure taxonomy
"""
from __future__ import annotations

from typing import Any

_DEFINITION = (
    "minimal observable process success from generation/extraction/execution artifact fields"
)


def compute_minimal_process_metrics_from_sections(
    generation: dict[str, Any],
    execution: dict[str, Any],
) -> dict[str, Any]:
    """Compute minimal observable process metrics from generation and execution sections.

    Parameters
    ----------
    generation:
        generation section dict (expects extraction_status, has_extracted_code)
    execution:
        execution section dict (expects execution_performed, tests_passed,
        error_type, timed_out)

    Returns
    -------
    dict with minimal observable process metric fields.
    is_full_process_reliability_metric is always False.
    process_failure_stage is "unknown" when required fields are missing.
    """
    if not isinstance(generation, dict) or not isinstance(execution, dict):
        return _unknown_metrics()

    extraction_status = generation.get("extraction_status")
    has_extracted_code = generation.get("has_extracted_code")
    execution_performed = execution.get("execution_performed")
    tests_passed = execution.get("tests_passed")
    error_type = execution.get("error_type")
    timed_out = execution.get("timed_out")

    # True iff extraction_status field is present in the generation section.
    generation_completed = "extraction_status" in generation

    # True iff extraction_status == "success" AND has_extracted_code is True.
    code_extraction_success = (
        extraction_status == "success" and has_extracted_code is True
    )

    # True iff execution_performed is True.
    execution_attempted = execution_performed is True

    # True iff execution_performed is True AND timed_out is False.
    execution_completed = execution_performed is True and timed_out is False

    # True iff tests_passed is True, timed_out is False, and error_type is None.
    execution_success = (
        tests_passed is True and timed_out is False and error_type is None
    )

    timeout_observed = timed_out is True
    runtime_error_observed = error_type == "runtime_error"

    # "generation" is reserved for future missing generation artifact / batch pipeline.
    # "unknown" when required fields are absent (generation_completed is False).
    if not generation_completed:
        process_failure_stage = "unknown"
    elif not code_extraction_success:
        process_failure_stage = "extraction"
    elif not execution_success:
        process_failure_stage = "execution"
    else:
        process_failure_stage = "completed"

    observable_process_success = (
        generation_completed
        and code_extraction_success
        and execution_attempted
        and execution_completed
        and execution_success
    )

    return {
        "generation_completed": generation_completed,
        "code_extraction_success": code_extraction_success,
        "execution_attempted": execution_attempted,
        "execution_completed": execution_completed,
        "execution_success": execution_success,
        "timeout_observed": timeout_observed,
        "runtime_error_observed": runtime_error_observed,
        "process_failure_stage": process_failure_stage,
        "observable_process_success": observable_process_success,
        "is_full_process_reliability_metric": False,
        "definition": _DEFINITION,
    }


def compute_minimal_process_metrics(summary: dict[str, Any]) -> dict[str, Any]:
    """Compute minimal observable process metrics from a run summary dict.

    Convenience wrapper around compute_minimal_process_metrics_from_sections.

    Parameters
    ----------
    summary:
        A run summary dict containing 'generation' and 'execution' sections.
        Missing or non-dict sections are treated as empty dicts, which yields
        process_failure_stage == "unknown".
    """
    if not isinstance(summary, dict):
        return _unknown_metrics()
    generation = summary.get("generation")
    if not isinstance(generation, dict):
        generation = {}
    execution = summary.get("execution")
    if not isinstance(execution, dict):
        execution = {}
    return compute_minimal_process_metrics_from_sections(generation, execution)


def _unknown_metrics() -> dict[str, Any]:
    """Return all-False metrics with process_failure_stage='unknown'."""
    return {
        "generation_completed": False,
        "code_extraction_success": False,
        "execution_attempted": False,
        "execution_completed": False,
        "execution_success": False,
        "timeout_observed": False,
        "runtime_error_observed": False,
        "process_failure_stage": "unknown",
        "observable_process_success": False,
        "is_full_process_reliability_metric": False,
        "definition": _DEFINITION,
    }
