"""
Generation artifact writer for Benchmark-3 generation-only LLM runs.

Writes per-task JSON artifacts and manifest.json to outputs/predictions/{run_id}/.
No secrets. No API keys. No execution results. No Docker. No sandbox.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reliability_harness.runtime.generation.code_extractor import CodeExtractionResult


def build_task_artifact(
    *,
    run_id: str,
    benchmark: str,
    task: Any,
    model_name: str,
    prompt: str,
    raw_response: str,
    extraction: CodeExtractionResult,
) -> dict[str, Any]:
    """Build a task artifact dict. Never records API key or secrets."""
    return {
        "run_id": run_id,
        "benchmark": benchmark,
        "task_id": task.task_id,
        "model_name": model_name,
        "prompt": prompt,
        "raw_response": raw_response,
        "extracted_code": extraction.extracted_code,
        "extraction_status": extraction.extraction_status,
        "error": extraction.error,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "llm_used": True,
        "docker_used": False,
        "execution_performed": False,
    }


def write_task_artifact(artifact: dict[str, Any], run_dir: Path) -> str:
    """Write a single task artifact to {run_dir}/{task_id}.json.

    Returns the absolute path of the written file.
    """
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    task_id_safe = str(artifact["task_id"]).replace("/", "_").replace(" ", "_")
    path = run_dir / f"{task_id_safe}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2, ensure_ascii=False)
    return str(path)


def write_manifest(
    *,
    run_id: str,
    benchmark: str,
    model_name: str,
    num_tasks: int,
    artifact_paths: list[str],
    run_dir: Path,
) -> dict[str, Any]:
    """Write manifest.json to {run_dir}/manifest.json and return the manifest dict.

    The returned dict includes a 'manifest_path' key with the absolute path.
    """
    run_dir = Path(run_dir)
    manifest: dict[str, Any] = {
        "run_id": run_id,
        "benchmark": benchmark,
        "model_name": model_name,
        "num_tasks": num_tasks,
        "artifacts": artifact_paths,
        "llm_used": True,
        "docker_used": False,
        "execution_performed": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    manifest_path = run_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
