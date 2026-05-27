"""Generation-to-execution integration helper — Benchmark-4C.1.

Connects a Benchmark-3 per-task generation artifact to the Benchmark-4
execution contract:

  generation artifact (JSON)
    -> extracted_code + BenchmarkTask.tests
    -> ExecutionInput
    -> execute_in_docker (or execute_locally)
    -> ExecutionResult
    -> ExecutionArtifact (written to outputs/executions/)

No LLM. No memory. No retry. No closed_loop_runner. No CLI wiring.
run_benchmark.py is unchanged by this module.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from reliability_harness.artifacts.execution_artifact import (
    build_execution_artifact,
    write_execution_artifact,
)
from reliability_harness.benchmarks.registry import get_adapter
from reliability_harness.runtime.execution.contract import ExecutionInput
from reliability_harness.runtime.execution.docker_runner import execute_in_docker
from reliability_harness.runtime.execution.local_runner import execute_locally
from reliability_harness.utils.paths import OUTPUTS_ROOT

_DEFAULT_EXECUTIONS_ROOT = OUTPUTS_ROOT / "executions"


class ExecutionIntegrationError(Exception):
    """Raised when a generation artifact cannot be executed.

    Scenarios:
    - artifact JSON unreadable
    - extraction_status != "success"
    - extracted_code missing or empty
    - benchmark missing
    - task_id missing
    - task_id not found in benchmark adapter
    """


def execute_generation_artifact(
    generation_artifact_path: "str | Path",
    *,
    output_root: Optional[Path] = None,
    backend: Any = None,
    use_docker: bool = True,
    timeout_ms: int = 10000,
) -> dict[str, Any]:
    """Load a generation artifact, execute its code, and write an execution artifact.

    Parameters
    ----------
    generation_artifact_path:
        Path to a per-task generation artifact JSON produced by Benchmark-3.
    output_root:
        Directory under which the execution artifact subdirectory is created.
        Defaults to outputs/executions/.
    backend:
        Optional DockerExecutionBackend-compatible object injected for testing.
        Ignored when use_docker=False.
    use_docker:
        If True (default), run via execute_in_docker.
        If False, run via execute_locally (trusted fixture code only).

    Returns
    -------
    dict with keys: generation_artifact_path, execution_artifact_path, run_id,
    benchmark, task_id, model_name, extraction_status, runner_type,
    docker_used, execution_performed, tests_passed, error_type.

    Raises
    ------
    ExecutionIntegrationError on any validation failure.
    """
    path = Path(generation_artifact_path)

    # ── 1. Read artifact ──────────────────────────────────────────────────────
    try:
        with open(path, encoding="utf-8") as f:
            gen_artifact = json.load(f)
    except Exception as exc:
        raise ExecutionIntegrationError(
            f"Cannot read generation artifact at {path}: {exc}"
        ) from exc

    # ── 2. Validate ───────────────────────────────────────────────────────────
    extraction_status = gen_artifact.get("extraction_status")
    if extraction_status != "success":
        raise ExecutionIntegrationError(
            f"extraction_status is {extraction_status!r}, expected 'success'. "
            f"Artifact cannot be executed: {path}"
        )

    extracted_code = gen_artifact.get("extracted_code") or ""
    if not extracted_code.strip():
        raise ExecutionIntegrationError(
            f"extracted_code is empty or missing in artifact: {path}"
        )

    benchmark = gen_artifact.get("benchmark") or ""
    if not benchmark:
        raise ExecutionIntegrationError(
            f"benchmark field is missing or empty in artifact: {path}"
        )

    task_id = gen_artifact.get("task_id") or ""
    if not task_id:
        raise ExecutionIntegrationError(
            f"task_id field is missing or empty in artifact: {path}"
        )

    run_id = gen_artifact.get("run_id") or "unknown_run"
    model_name = gen_artifact.get("model_name") or "unknown"

    # ── 3. Locate BenchmarkTask ───────────────────────────────────────────────
    try:
        adapter = get_adapter(benchmark)
        tasks = adapter.load_tasks()
    except ValueError as exc:
        raise ExecutionIntegrationError(
            f"Cannot load adapter for benchmark {benchmark!r}: {exc}"
        ) from exc

    task = next((t for t in tasks if t.task_id == task_id), None)
    if task is None:
        available = [t.task_id for t in tasks]
        raise ExecutionIntegrationError(
            f"task_id {task_id!r} not found in benchmark {benchmark!r}. "
            f"Available task_ids: {available}"
        )

    # ── 4. Build ExecutionInput ───────────────────────────────────────────────
    exec_run_id = f"{run_id}_exec"
    exec_input = ExecutionInput(
        run_id=exec_run_id,
        benchmark=benchmark,
        task_id=task_id,
        candidate_code=extracted_code,
        tests=task.tests,
        timeout_ms=timeout_ms,
        docker_used=use_docker,
        source_generation_artifact=str(path),
    )

    # ── 5. Execute ────────────────────────────────────────────────────────────
    if use_docker:
        result = execute_in_docker(exec_input, backend=backend)
    else:
        result = execute_locally(exec_input)

    # ── 6. Write execution artifact ───────────────────────────────────────────
    executions_root = Path(output_root) if output_root is not None else _DEFAULT_EXECUTIONS_ROOT
    output_dir = executions_root / exec_run_id
    artifact = build_execution_artifact(exec_input, result)
    artifact_path = write_execution_artifact(artifact, output_dir)

    # ── 7. Return summary ─────────────────────────────────────────────────────
    return {
        "generation_artifact_path": str(path),
        "execution_artifact_path": str(artifact_path),
        "run_id": exec_run_id,
        "benchmark": benchmark,
        "task_id": task_id,
        "model_name": model_name,
        "extraction_status": extraction_status,
        "runner_type": "docker" if use_docker else "local",
        "docker_used": result.docker_used,
        "execution_performed": result.execution_performed,
        "tests_passed": result.tests_passed,
        "error_type": result.error_type,
    }
