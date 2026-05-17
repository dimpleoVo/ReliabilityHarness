import json
import os
from datetime import datetime

from app.reasoning.trajectory_analyzer import analyze_trajectory

# Default save location: ReActX/runs/ (two levels above this file)
_DEFAULT_RUNS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "runs")
)


def _extract_attempt(entry: dict) -> dict:
    step = entry.get("step", 0)
    traj = entry.get("traj") or {}
    eval_result = entry.get("eval") or {}
    prompt_input = entry.get("input", "")

    steps = traj.get("steps") or []
    last_step = steps[-1] if steps else {}
    sandbox = last_step.get("sandbox") or {}

    runtime_error = sandbox.get("runtime_error", eval_result.get("runtime_error", False))
    score = eval_result.get("score")

    if runtime_error:
        retry_reason = "runtime_error"
    elif score is not None and score > 0:
        retry_reason = "semantic_error"
    else:
        retry_reason = None

    failure = (eval_result.get("failure") or {})

    return {
        "attempt_index": step,
        "generated_code": last_step.get("generated_code", ""),
        "stdout": sandbox.get("stdout", ""),
        "stderr": sandbox.get("stderr", ""),
        "runtime_error": runtime_error,
        "timeout": sandbox.get("timeout", False),
        "score": score,
        "evaluation": {
            "source": eval_result.get("source"),
            "metrics": eval_result.get("metrics"),
            "failure_summary": failure.get("failure_summary", []),
            "runtime_error": eval_result.get("runtime_error", False),
        },
        "reflection": prompt_input if step > 1 else None,
        "retry_reason": retry_reason,
    }


def _analysis_score(attempt: dict) -> float:
    if attempt.get("runtime_error") or attempt.get("timeout"):
        return 0.0

    raw_score = attempt.get("score")
    metrics = (attempt.get("evaluation") or {}).get("metrics") or {}
    edit_distance = metrics.get("edit_distance")

    if edit_distance == 0 or raw_score == 0:
        return 1.0

    try:
        return float(raw_score or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _build_trajectory_analysis(attempts: list[dict]) -> dict | None:
    if not attempts:
        return None

    try:
        reasoning_attempts = []
        for attempt in attempts:
            reasoning_attempt = dict(attempt)
            reasoning_attempt["score"] = _analysis_score(attempt)
            reasoning_attempts.append(reasoning_attempt)
        return analyze_trajectory(reasoning_attempts)
    except Exception as e:
        print(f"[Artifact] WARNING: trajectory analysis failed: {e}")
        return None


def save_run_artifact(result: dict, task: str, runs_dir: str | None = None) -> str | None:
    """
    Persist a run artifact to disk. Never raises — failures are printed as warnings.
    Returns the file path on success, None on failure.
    """
    try:
        target_dir = runs_dir or _DEFAULT_RUNS_DIR
        os.makedirs(target_dir, exist_ok=True)

        timestamp = datetime.now()
        filename = f"run_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(target_dir, filename)

        trajectory_all = result.get("trajectory") or []
        reliability_report = result.get("reliability_report") or {}
        final_eval = (trajectory_all[-1].get("eval") or {}) if trajectory_all else {}
        failure = (final_eval.get("failure") or {})

        attempts = [_extract_attempt(entry) for entry in trajectory_all]

        artifact = {
            "task": task,
            "timestamp": timestamp.isoformat(),
            "success": result.get("success", False),
            "num_attempts": result.get("total_steps", len(trajectory_all)),
            "final_score": reliability_report.get("final_score"),
            "failure_summary": failure.get("failure_summary", []),
            "memory_used": reliability_report.get("used_memory", False),
            "attempts": attempts,
            "trajectory_analysis": _build_trajectory_analysis(attempts),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(artifact, f, indent=2, ensure_ascii=False)

        print(f"[Artifact] Saved: {filepath}")
        return filepath

    except Exception as e:
        print(f"[Artifact] WARNING: failed to save run artifact: {e}")
        return None
