"""
Generator: drives LLM candidate generation for a list of BenchmarkTask instances.

No Docker. No sandbox. No execution. No retry. No memory. No process metrics.
Writes per-task artifacts and manifest.json to outputs/predictions/{run_id}/.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reliability_harness.benchmarks.task_schema import BenchmarkTask
from reliability_harness.runtime.generation.prompt_builder import build_generation_prompt
from reliability_harness.runtime.generation.code_extractor import (
    CodeExtractionResult,
    extract_python_code,
)
from reliability_harness.artifacts.generation_artifact import (
    build_task_artifact,
    write_task_artifact,
    write_manifest,
)
from reliability_harness.utils.paths import PREDICTIONS_ROOT


def generate_for_tasks(
    tasks: list[BenchmarkTask],
    llm_client: Any,
    model_name: str,
    output_root: Path | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Generate candidate code for each task using the provided LLM client.

    Parameters
    ----------
    tasks:
        List of BenchmarkTask instances to generate for.
    llm_client:
        Object with a generate(prompt: str) -> str method.
    model_name:
        Model identifier to record in artifacts (never the API key).
    output_root:
        Root directory for predictions. Defaults to outputs/predictions/.
    limit:
        If set, only process the first `limit` tasks.

    Returns
    -------
    dict
        Manifest dict including a 'manifest_path' key pointing to manifest.json.
    """
    if output_root is None:
        output_root = PREDICTIONS_ROOT

    if limit is not None:
        tasks = list(tasks)[:limit]

    run_id = (
        datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        + "_"
        + uuid.uuid4().hex[:8]
    )
    run_dir = Path(output_root) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    benchmark = tasks[0].benchmark if tasks else "unknown"
    artifact_paths: list[str] = []

    for task in tasks:
        prompt = build_generation_prompt(task)
        error_msg: str | None = None
        raw_response = ""

        try:
            raw_response = llm_client.generate(prompt)
        except Exception as exc:
            error_msg = str(exc)

        if error_msg:
            extraction = CodeExtractionResult(
                extracted_code=None,
                extraction_status="error",
                error=error_msg,
            )
        else:
            extraction = extract_python_code(raw_response)

        artifact = build_task_artifact(
            run_id=run_id,
            benchmark=benchmark,
            task=task,
            model_name=model_name,
            prompt=prompt,
            raw_response=raw_response,
            extraction=extraction,
        )
        artifact_path = write_task_artifact(artifact, run_dir)
        artifact_paths.append(artifact_path)

    return write_manifest(
        run_id=run_id,
        benchmark=benchmark,
        model_name=model_name,
        num_tasks=len(tasks),
        artifact_paths=artifact_paths,
        run_dir=run_dir,
    )
