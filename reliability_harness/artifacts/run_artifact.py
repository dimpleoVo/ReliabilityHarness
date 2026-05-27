import json
import os
from datetime import datetime

from reliability_harness.reasoning.trajectory_analyzer import analyze_trajectory
from reliability_harness.utils.paths import RUNS_ROOT

# Default save location: outputs/runs/ (resolved via paths.RUNS_ROOT, independent of cwd)
_DEFAULT_RUNS_DIR = RUNS_ROOT


def _derive_final_success(entry: dict, runtime_error: bool, score, eval_result: dict) -> bool | None:
    # Prefer explicit step_success stored by closed_loop_runner
    step_success_explicit = entry.get("step_success")
    if step_success_explicit is not None:
        return bool(step_success_explicit)

    if runtime_error:
        return False

    metrics = eval_result.get("metrics") or {}
    judge = eval_result.get("judge") or {}

    if judge.get("correct") is not None:
        return bool(judge["correct"])

    llm_judge_score = metrics.get("llm_judge")
    if llm_judge_score is not None:
        return float(llm_judge_score) >= 0.8

    # Explicit outcome fields from eval_result (future extensibility)
    for field in ("final_success", "task_success", "test_passed", "tests_passed", "success"):
        val = eval_result.get(field)
        if val is not None:
            return bool(val)

    # No explicit success signal: return None (unknown, not derived from edit_distance)
    return None


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
    final_success = _derive_final_success(entry, runtime_error, score, eval_result)

    return {
        "attempt_index": step,
        "generated_code": last_step.get("generated_code", ""),
        "stdout": sandbox.get("stdout", ""),
        "stderr": sandbox.get("stderr", ""),
        "runtime_error": runtime_error,
        "timeout": sandbox.get("timeout", False),
        "score": score,
        "final_success": final_success,
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

    # Prefer explicit final_success boolean (avoids direction ambiguity)
    if "final_success" in attempt:
        return 1.0 if attempt["final_success"] else 0.0

    # Legacy fallback for artifacts that pre-date final_success field
    raw_score = attempt.get("score")
    metrics = (attempt.get("evaluation") or {}).get("metrics") or {}
    edit_distance = metrics.get("edit_distance")

    # edit_distance=0 or LLM-judge score=0 both mean success
    if edit_distance == 0 or raw_score == 0:
        return 1.0

    return 0.0  # conservative: treat any other score as failure


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

        final_success = result.get("final_success", result.get("success", False))
        task_success = result.get("task_success", final_success)
        recovery_success = result.get("recovery_success", False)
        initially_failed = result.get("initially_failed", False)

        artifact = {
            "task": task,
            "timestamp": timestamp.isoformat(),
            "success": result.get("success", False),  # compat
            "final_success": final_success,
            "task_success": task_success,
            "initially_failed": initially_failed,
            "recovery_success": recovery_success,
            "num_attempts": result.get("total_steps", len(trajectory_all)),
            "final_score": reliability_report.get("final_score"),  # compat
            "score_semantics": "legacy_compat",
            "primary_metric_name": "final_success",
            "primary_metric_direction": "boolean",
            "primary_success_field": "final_success",
            "legacy_score_metric_name": "edit_distance",
            "legacy_score_metric_direction": "lower_is_better",
            "auxiliary_metrics": final_eval.get("metrics") or {},
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
