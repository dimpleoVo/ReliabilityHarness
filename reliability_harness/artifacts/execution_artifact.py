"""Execution artifact writer for Benchmark-4A.1.

Writes per-execution JSON artifacts to outputs/executions/{run_id}/.
Never records .env, API keys, provider tokens, or full environment variables.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reliability_harness.runtime.execution.contract import ExecutionInput, ExecutionResult

_ARTIFACT_VERSION = "4A.1"


def build_execution_artifact(
    input: ExecutionInput,
    result: ExecutionResult,
) -> dict[str, Any]:
    """Build an execution artifact dict. Never records secrets."""
    return {
        "artifact_version": _ARTIFACT_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_id": input.run_id,
        "benchmark": input.benchmark,
        "task_id": input.task_id,
        "candidate_code": input.candidate_code,
        "tests": input.tests,
        "source_generation_artifact": input.source_generation_artifact,
        "result": {
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timed_out": result.timed_out,
            "tests_passed": result.tests_passed,
            "error_type": result.error_type,
            "execution_time_ms": result.execution_time_ms,
            "docker_used": result.docker_used,
            "execution_performed": result.execution_performed,
        },
    }


def write_execution_artifact(artifact: dict[str, Any], output_dir: Path) -> Path:
    """Write artifact to {output_dir}/{run_id}_{task_id}.json.

    Returns the path of the written file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id_safe = str(artifact["run_id"]).replace("/", "_").replace(" ", "_")
    task_id_safe = str(artifact["task_id"]).replace("/", "_").replace(" ", "_")
    path = output_dir / f"{run_id_safe}_{task_id_safe}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2, ensure_ascii=False)
    return path
