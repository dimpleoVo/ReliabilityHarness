"""Run summary artifact builder — Benchmark-4D.1 stable envelope +
Benchmark-5A minimal observable process metrics +
Benchmark-5B minimal observable failure diagnostics.

Aggregates a generation artifact and its corresponding execution artifact into a
lightweight, extensible single-run summary.

Design: stable envelope + extensible sections
  - Top-level structure is stable and versioned.
  - metrics.process is automatically populated with minimal observable process
    signals (Benchmark-5A).  These are NOT full process reliability metrics.
  - diagnostics.failure is automatically populated with minimal observable failure
    diagnostics (Benchmark-5B).  These are NOT a full failure taxonomy.
  - metrics.recovery / metrics.memory are empty extension points.
  - Large raw fields (prompt, raw_response, extracted_code, candidate_code, stdout, stderr)
    are NOT copied; the summary only stores path references to the source artifacts.

final_success definition:
  extraction_status == "success" AND execution_performed is True AND tests_passed is True

  final_success is a final execution success proxy, not a process reliability metric.
  The core thesis of this paper is that final task success does not fully reflect
  agent reliability — process metrics are required for that.

Not in scope (Benchmark-5B boundaries):
  - CLI / run_benchmark wiring changes
  - batch / manifest / directory summary
  - root-cause analysis, reasoning trace, LLM-as-judge, full failure taxonomy
  - reasoning consistency, tool correctness, retry/recovery, memory-assisted recovery
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reliability_harness.diagnostics.failure_diagnostics import (
    compute_minimal_failure_diagnostics_from_sections,
)
from reliability_harness.metrics.process_metrics import (
    compute_minimal_process_metrics_from_sections,
)
from reliability_harness.utils.paths import ARTIFACTS_ROOT

_ARTIFACT_VERSION = "4D.1"
_RUN_SUMMARIES_ROOT = ARTIFACTS_ROOT / "run_summaries"

_REQUIRED_GENERATION_FIELDS = ("run_id", "benchmark", "task_id", "model_name", "extraction_status")
_REQUIRED_EXECUTION_RESULT_FIELDS = (
    "execution_performed",
    "tests_passed",
    "docker_used",
    "error_type",
    "timed_out",
    "execution_time_ms",
)


class RunSummaryError(ValueError):
    """Raised when run summary cannot be built due to missing or inconsistent data."""


def load_json(path: str | Path) -> dict[str, Any]:
    """Load a JSON artifact from disk. Raises RunSummaryError on failure."""
    p = Path(path)
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise RunSummaryError(f"Artifact file not found: {p}") from exc
    except json.JSONDecodeError as exc:
        raise RunSummaryError(f"Artifact file is not valid JSON: {p}") from exc


def _safe_task_id(task_id: str) -> str:
    """Replace path-unsafe characters with underscores for use in filenames."""
    return re.sub(r"[/\\:\s]", "_", task_id)


def _validate_generation(artifact: dict[str, Any]) -> None:
    missing = [f for f in _REQUIRED_GENERATION_FIELDS if f not in artifact]
    if missing:
        raise RunSummaryError(
            f"Generation artifact is missing required fields: {missing}"
        )


def _validate_execution(artifact: dict[str, Any]) -> None:
    if "result" not in artifact:
        raise RunSummaryError(
            "Execution artifact is missing required 'result' field."
        )
    result = artifact["result"]
    missing = [f for f in _REQUIRED_EXECUTION_RESULT_FIELDS if f not in result]
    if missing:
        raise RunSummaryError(
            f"Execution artifact result is missing required fields: {missing}"
        )


def _validate_identity_consistency(gen: dict[str, Any], exec_: dict[str, Any]) -> None:
    """Raise RunSummaryError if benchmark or task_id mismatch between artifacts."""
    gen_benchmark = gen.get("benchmark")
    exec_benchmark = exec_.get("benchmark")
    if exec_benchmark is not None and gen_benchmark != exec_benchmark:
        raise RunSummaryError(
            f"Benchmark mismatch: generation={gen_benchmark!r}, "
            f"execution={exec_benchmark!r}"
        )
    gen_task_id = gen.get("task_id")
    exec_task_id = exec_.get("task_id")
    if exec_task_id is not None and gen_task_id != exec_task_id:
        raise RunSummaryError(
            f"task_id mismatch: generation={gen_task_id!r}, "
            f"execution={exec_task_id!r}"
        )


def build_run_summary(
    generation_artifact: dict[str, Any],
    execution_artifact: dict[str, Any],
    *,
    generation_artifact_path: str | Path,
    execution_artifact_path: str | Path,
) -> dict[str, Any]:
    """Build a single-run summary dict from a generation and execution artifact pair.

    Does NOT copy large raw fields (prompt, raw_response, extracted_code,
    candidate_code, stdout, stderr) — only path references are stored.

    final_success is a final execution success proxy, not a process reliability metric.

    Parameters
    ----------
    generation_artifact:
        Dict loaded from a per-task generation artifact JSON (Benchmark-3 schema).
    execution_artifact:
        Dict loaded from a per-task execution artifact JSON (Benchmark-4A schema).
    generation_artifact_path:
        Filesystem path of the generation artifact (stored as reference only).
    execution_artifact_path:
        Filesystem path of the execution artifact (stored as reference only).

    Returns
    -------
    dict
        Versioned run summary with stable envelope and extensible sections.

    Raises
    ------
    RunSummaryError
        When required fields are missing or benchmark/task_id are inconsistent.
    """
    _validate_generation(generation_artifact)
    _validate_execution(execution_artifact)
    _validate_identity_consistency(generation_artifact, execution_artifact)

    result = execution_artifact["result"]

    extraction_status = generation_artifact["extraction_status"]
    execution_performed = bool(result["execution_performed"])
    tests_passed = bool(result["tests_passed"])

    # final_success is a final execution success proxy.
    # It is NOT a process reliability metric — see paper thesis.
    final_success = (
        extraction_status == "success"
        and execution_performed is True
        and tests_passed is True
    )

    runner_type = result.get("runner_type", "docker" if result.get("docker_used") else "local")

    generation_section = {
        "extraction_status": extraction_status,
        "has_extracted_code": bool(generation_artifact.get("extracted_code")),
    }
    execution_section = {
        "execution_performed": execution_performed,
        "runner_type": runner_type,
        "docker_used": bool(result["docker_used"]),
        "tests_passed": tests_passed,
        "error_type": result["error_type"],
        "timed_out": bool(result["timed_out"]),
        "execution_time_ms": result["execution_time_ms"],
    }
    process_metrics = compute_minimal_process_metrics_from_sections(
        generation_section, execution_section
    )
    failure_diagnostics = compute_minimal_failure_diagnostics_from_sections(
        generation_section, execution_section, metrics_process=process_metrics
    )

    return {
        "artifact_version": _ARTIFACT_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "identity": {
            "run_id": generation_artifact["run_id"],
            "benchmark": generation_artifact["benchmark"],
            "task_id": generation_artifact["task_id"],
            "model_name": generation_artifact["model_name"],
        },
        "artifact_refs": {
            "generation_artifact_path": str(generation_artifact_path),
            "execution_artifact_path": str(execution_artifact_path),
        },
        "generation": generation_section,
        "execution": execution_section,
        "success": {
            # final_success is a final execution success proxy, not a process reliability metric.
            "final_success": final_success,
            "definition": (
                "extraction_status == success "
                "AND execution_performed == true "
                "AND tests_passed == true"
            ),
            "is_process_reliability_metric": False,
        },
        "metrics": {
            "process": process_metrics,
            "recovery": {},
            "memory": {},
        },
        "diagnostics": {
            "failure": failure_diagnostics,
        },
        "limitations": [
            (
                "final_success is a final execution success proxy, "
                "not a process reliability metric"
            ),
            (
                "metrics.process contains minimal observable signals only (Benchmark-5A); "
                "reasoning consistency, tool correctness, retry/recovery, "
                "memory-assisted recovery, and LLM-as-judge are not implemented"
            ),
            (
                "diagnostics.failure contains minimal observable diagnostics only "
                "(Benchmark-5B); root-cause analysis, reasoning trace, LLM-as-judge, "
                "and full failure taxonomy are not implemented"
            ),
            (
                "metrics.recovery and metrics.memory are empty "
                "(Benchmark-4D.1 extension points, not yet populated)"
            ),
        ],
    }


def write_run_summary(
    summary: dict[str, Any],
    output_dir: Path | None = None,
) -> Path:
    """Write a run summary dict to disk and return the path.

    Default output directory: outputs/artifacts/run_summaries/
    Filename pattern: {run_id}_{task_id}_summary.json
    task_id path-unsafe characters (/ \\ : space) are replaced with _.
    """
    if output_dir is None:
        output_dir = _RUN_SUMMARIES_ROOT

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    identity = summary.get("identity", {})
    run_id_safe = re.sub(r"[/\\:\s]", "_", str(identity.get("run_id", "unknown")))
    task_id_safe = _safe_task_id(str(identity.get("task_id", "unknown")))

    path = output_dir / f"{run_id_safe}_{task_id_safe}_summary.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    return path


def build_run_summary_from_paths(
    generation_artifact_path: str | Path,
    execution_artifact_path: str | Path,
) -> dict[str, Any]:
    """Convenience wrapper: load both artifacts from disk and build a summary.

    Raises RunSummaryError if either file is unreadable or required fields are missing.
    """
    gen = load_json(generation_artifact_path)
    exec_ = load_json(execution_artifact_path)
    return build_run_summary(
        gen,
        exec_,
        generation_artifact_path=generation_artifact_path,
        execution_artifact_path=execution_artifact_path,
    )
