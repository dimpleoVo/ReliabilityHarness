import json
import os
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
TASKS_PATH = BASE_DIR / "data" / "reliability_tasks.json"
RESULTS_DIR = BASE_DIR / "benchmark_results"
RESULTS_JSON = RESULTS_DIR / "benchmark_results.json"
RESULTS_MD = RESULTS_DIR / "benchmark_results.md"

REQUIRED_RESULT_FIELDS = (
    "id",
    "category",
    "task",
    "expected_output",
    "success",
    "num_attempts",
    "final_output",
    "final_score",
    "failure_mode",
    "runtime_error",
    "timeout",
    "recovered",
    "artifact_path",
    "error_summary",
)

DEFAULT_CATEGORIES = (
    "runtime_error",
    "timeout",
    "semantic_error",
    "recoverable_retry",
    "memory_assisted",
)


def _parse_limit(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        limit = int(value)
    except ValueError:
        raise ValueError(f"BENCHMARK_LIMIT must be an integer, got: {value!r}")
    if limit < 0:
        raise ValueError("BENCHMARK_LIMIT must be >= 0")
    return limit


def load_tasks(path: Path = TASKS_PATH, limit: int | None = None) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    if not isinstance(tasks, list):
        raise ValueError("reliability_tasks.json must contain a JSON list")

    if limit is not None:
        return tasks[:limit]
    return tasks


def _normalize_output(text: Any) -> str:
    return str(text or "").strip()


def _exact_match_score(expected: Any, actual: Any) -> float:
    return 1.0 if _normalize_output(expected) == _normalize_output(actual) else 0.0


def _artifact_path(output_dir: Path, task_id: str) -> Path:
    return output_dir / "artifacts" / f"{task_id}.json"


def _write_task_artifact(output_dir: Path, task_id: str, payload: dict[str, Any]) -> str:
    path = _artifact_path(output_dir, task_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return str(path)


def run_task_mock(task: dict[str, Any], output_dir: Path = RESULTS_DIR) -> dict[str, Any]:
    task_id = str(task.get("id", "unknown"))
    category = str(task.get("category", "unknown"))
    expected = task.get("expected_output", "")

    if category == "recoverable_retry":
        # Simulates: attempt 1 fails (semantic), attempt 2 succeeds via reflection.
        num_attempts = 2
        success = True
        recovered = True
        final_output = expected
        runtime_error = False
        timeout = False
        error_summary = ""
    else:
        should_fail = task_id.endswith("_004") or category == "timeout"
        num_attempts = 3 if should_fail else 1
        final_output = expected if not should_fail else ""
        success = not should_fail
        recovered = False
        runtime_error = category == "runtime_error" and not success
        timeout = category == "timeout" and not success
        error_summary = "" if success else f"mock_{category}_failure"

    final_score = _exact_match_score(expected, final_output)

    result = {
        "id": task_id,
        "category": category,
        "task": task.get("task", ""),
        "expected_output": expected,
        "success": success,
        "num_attempts": num_attempts,
        "final_output": final_output,
        "final_score": final_score,
        "failure_mode": task.get("failure_mode", category),
        "runtime_error": runtime_error,
        "timeout": timeout,
        "recovered": recovered,
        "artifact_path": "",
        "error_summary": error_summary,
    }
    result["artifact_path"] = _write_task_artifact(
        output_dir,
        task_id,
        {"task": task, "result": result, "mock": True},
    )
    return result


def _last_attempt(closed_loop_result: dict[str, Any]) -> dict[str, Any]:
    attempts = closed_loop_result.get("trajectory") or []
    if not attempts:
        return {}
    return attempts[-1] or {}


def _first_attempt(closed_loop_result: dict[str, Any]) -> dict[str, Any]:
    attempts = closed_loop_result.get("trajectory") or []
    if not attempts:
        return {}
    return attempts[0] or {}


def _attempt_eval(attempt: dict[str, Any]) -> dict[str, Any]:
    return attempt.get("eval") or {}


def _attempt_last_step(attempt: dict[str, Any]) -> dict[str, Any]:
    traj = attempt.get("traj") or {}
    steps = traj.get("steps") or []
    if not steps:
        return {}
    return steps[-1] or {}


def _extract_timeout(closed_loop_result: dict[str, Any]) -> bool:
    taxonomy = closed_loop_result.get("failure_taxonomy") or {}
    if "timeout" in (taxonomy.get("failure_types") or []):
        return True

    for attempt in closed_loop_result.get("trajectory") or []:
        sandbox = _attempt_last_step(attempt).get("sandbox") or {}
        if sandbox.get("timeout"):
            return True
    return False


def _extract_error_summary(closed_loop_result: dict[str, Any]) -> str:
    taxonomy = closed_loop_result.get("failure_taxonomy") or {}
    failure_types = taxonomy.get("failure_types") or []
    if failure_types:
        return ", ".join(str(x) for x in failure_types)

    report = closed_loop_result.get("reliability_report") or {}
    if report.get("error_type"):
        return str(report["error_type"])

    last = _attempt_last_step(_last_attempt(closed_loop_result))
    return str(last.get("error") or "")


def run_task_real(task: dict[str, Any], output_dir: Path = RESULTS_DIR) -> dict[str, Any]:
    from app.loop.closed_loop_runner import is_eval_success, run_closed_loop

    task_id = str(task.get("id", "unknown"))
    expected = task.get("expected_output", "")
    closed_loop_result = run_closed_loop(task.get("task", ""))

    attempts = closed_loop_result.get("trajectory") or []
    num_attempts = len(attempts)
    final_output = _normalize_output(closed_loop_result.get("final_answer"))
    final_score = _exact_match_score(expected, final_output)
    success = final_score == 1.0 if expected is not None else bool(closed_loop_result.get("success"))

    first_eval = _attempt_eval(_first_attempt(closed_loop_result))
    recovered = bool(num_attempts > 1 and success and first_eval and not is_eval_success(first_eval))

    report = closed_loop_result.get("reliability_report") or {}
    last_eval = _attempt_eval(_last_attempt(closed_loop_result))

    result = {
        "id": task_id,
        "category": task.get("category", "unknown"),
        "task": task.get("task", ""),
        "expected_output": expected,
        "success": success,
        "num_attempts": num_attempts,
        "final_output": final_output,
        "final_score": final_score,
        "failure_mode": report.get("error_type") or task.get("failure_mode", ""),
        "runtime_error": bool(last_eval.get("runtime_error", report.get("runtime_error", False))),
        "timeout": _extract_timeout(closed_loop_result),
        "recovered": recovered,
        "artifact_path": "",
        "error_summary": _extract_error_summary(closed_loop_result),
    }
    result["artifact_path"] = _write_task_artifact(
        output_dir,
        task_id,
        {"task": task, "result": result, "closed_loop_result": closed_loop_result, "mock": False},
    )
    return result


def validate_task_result(result: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_RESULT_FIELDS if field not in result]
    if missing:
        raise ValueError(f"task result missing required fields: {missing}")


def aggregate_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    successes = sum(1 for r in results if r.get("success"))
    recovered = sum(1 for r in results if r.get("recovered"))
    runtime_errors = sum(1 for r in results if r.get("runtime_error"))
    timeouts = sum(1 for r in results if r.get("timeout"))
    attempts = sum(int(r.get("num_attempts") or 0) for r in results)

    categories = {cat: [] for cat in DEFAULT_CATEGORIES}
    for r in results:
        categories.setdefault(str(r.get("category", "unknown")), []).append(r)

    category_metrics = {}
    for category, rows in categories.items():
        count = len(rows)
        category_metrics[category] = {
            "total_tasks": count,
            "success_rate": round(sum(1 for r in rows if r.get("success")) / count, 4) if count else 0.0,
            "avg_attempts": round(sum(int(r.get("num_attempts") or 0) for r in rows) / count, 4) if count else 0.0,
            "recovery_rate": round(sum(1 for r in rows if r.get("recovered")) / count, 4) if count else 0.0,
            "runtime_error_rate": round(sum(1 for r in rows if r.get("runtime_error")) / count, 4) if count else 0.0,
            "timeout_rate": round(sum(1 for r in rows if r.get("timeout")) / count, 4) if count else 0.0,
        }

    return {
        "total_tasks": total,
        "success_rate": round(successes / total, 4) if total else 0.0,
        "avg_attempts": round(attempts / total, 4) if total else 0.0,
        "recovery_rate": round(recovered / total, 4) if total else 0.0,
        "runtime_error_rate": round(runtime_errors / total, 4) if total else 0.0,
        "timeout_rate": round(timeouts / total, 4) if total else 0.0,
        "category_metrics": category_metrics,
    }


def build_markdown_report(summary: dict[str, Any], results: list[dict[str, Any]]) -> str:
    lines = [
        "# Reliability Benchmark Results",
        "",
        f"- total tasks: {summary['total_tasks']}",
        f"- success rate: {summary['success_rate']}",
        f"- recovery rate: {summary['recovery_rate']}",
        f"- avg attempts: {summary['avg_attempts']}",
        f"- runtime error rate: {summary['runtime_error_rate']}",
        f"- timeout rate: {summary['timeout_rate']}",
        "",
        "## Category Summary",
        "",
        "| category | total | success_rate | recovery_rate | avg_attempts | runtime_error_rate | timeout_rate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for category, metrics in summary.get("category_metrics", {}).items():
        lines.append(
            "| {category} | {total_tasks} | {success_rate} | {recovery_rate} | "
            "{avg_attempts} | {runtime_error_rate} | {timeout_rate} |".format(
                category=category,
                **metrics,
            )
        )

    failed = [r for r in results if not r.get("success")]
    lines.extend(["", "## Failed Tasks", ""])
    if not failed:
        lines.append("- none")
    else:
        for r in failed:
            lines.append(
                f"- {r.get('id')} [{r.get('category')}]: {r.get('error_summary') or 'failed'}"
            )

    return "\n".join(lines) + "\n"


def write_benchmark_outputs(
    results: list[dict[str, Any]],
    summary: dict[str, Any],
    output_dir: Path = RESULTS_DIR,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "summary": summary,
        "results": results,
    }

    json_path = output_dir / "benchmark_results.json"
    md_path = output_dir / "benchmark_results.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(build_markdown_report(summary, results))

    return {
        "json": str(json_path),
        "markdown": str(md_path),
    }


def _load_mock_tasks(path: Path = TASKS_PATH, limit: int | None = None) -> list[dict[str, Any]]:
    """Load tasks for mock mode, guaranteeing one task per required category comes first."""
    all_tasks = load_tasks(path)
    by_category: dict[str, list[dict[str, Any]]] = {}
    for t in all_tasks:
        by_category.setdefault(str(t.get("category", "unknown")), []).append(t)

    seeds = [by_category[cat][0] for cat in DEFAULT_CATEGORIES if cat in by_category]
    seed_ids = {t["id"] for t in seeds}
    rest = [t for t in all_tasks if t["id"] not in seed_ids]

    combined = seeds + rest
    return combined[:limit] if limit is not None else combined


def run_benchmark(
    tasks_path: Path = TASKS_PATH,
    output_dir: Path = RESULTS_DIR,
    limit: int | None = None,
    mock: bool = False,
) -> dict[str, Any]:
    tasks = _load_mock_tasks(tasks_path, limit=limit) if mock else load_tasks(tasks_path, limit=limit)
    results = []

    for task in tasks:
        result = run_task_mock(task, output_dir=output_dir) if mock else run_task_real(task, output_dir=output_dir)
        validate_task_result(result)
        results.append(result)

    summary = aggregate_results(results)
    paths = write_benchmark_outputs(results, summary, output_dir=output_dir)

    return {
        "summary": summary,
        "results": results,
        "paths": paths,
    }


def main() -> None:
    limit = _parse_limit(os.environ.get("BENCHMARK_LIMIT"))
    mock = os.environ.get("BENCHMARK_MOCK") == "1"

    benchmark = run_benchmark(limit=limit, mock=mock)
    summary = benchmark["summary"]
    paths = benchmark["paths"]

    print("[ReliabilityBenchmark] completed")
    print(f"total_tasks={summary['total_tasks']}")
    print(f"success_rate={summary['success_rate']}")
    print(f"recovery_rate={summary['recovery_rate']}")
    print(f"avg_attempts={summary['avg_attempts']}")
    print(f"json={paths['json']}")
    print(f"markdown={paths['markdown']}")


if __name__ == "__main__":
    main()
