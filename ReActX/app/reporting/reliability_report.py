"""
Minimal reliability report generator.
Reads run_*.json artifacts from runs/ and writes JSON + Markdown to reports/.
No LLM, no database, no dashboard — pure file I/O and arithmetic.
"""
import json
import os
from collections import Counter
from pathlib import Path
from statistics import mean

# Resolved relative to this file: ReActX/runs/ and ReActX/reports/
_DEFAULT_RUNS_DIR = Path(__file__).parent.parent.parent / "runs"
_DEFAULT_REPORTS_DIR = Path(__file__).parent.parent.parent / "reports"


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def load_artifacts(runs_dir=None) -> list[dict]:
    """
    Load all run_*.json files from runs_dir.
    Skips unreadable / malformed files silently.
    Returns [] if directory is missing or empty.
    """
    target = Path(runs_dir) if runs_dir else _DEFAULT_RUNS_DIR
    if not target.exists():
        return []

    artifacts = []
    for path in sorted(target.glob("run_*.json")):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                artifacts.append(data)
        except Exception:
            pass  # skip malformed files silently
    return artifacts


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_metrics(artifacts: list[dict]) -> dict:
    """
    Aggregate reliability metrics from a list of run artifact dicts.
    All fields default gracefully — missing keys never crash.
    """
    empty = {
        "total_runs": 0,
        "success_rate": 0.0,
        "avg_attempts": 0.0,
        "runtime_error_rate": 0.0,
        "timeout_rate": 0.0,
        "memory_usage_rate": 0.0,
        "retry_trigger_rate": 0.0,
        "recovery_rate": 0.0,
        "recovery_rate_over_all_tasks": 0.0,
        "recovery_rate_over_failed_first_attempts": 0.0,
        "recovery_rate_over_retried_tasks": 0.0,
        "failure_type_distribution": {
            "runtime_error": 0,
            "semantic_error": 0,
            "timeout": 0,
            "unknown": 0,
        },
    }
    if not artifacts:
        return empty

    total = len(artifacts)

    def _artifact_success(r):
        # Prefer final_success; fall back to success for older artifacts
        if "final_success" in r:
            return bool(r["final_success"])
        return bool(r.get("success", False))

    # ── per-run counters ──────────────────────────────────────────────────
    successes      = sum(1 for r in artifacts if _artifact_success(r))
    memory_used    = sum(1 for r in artifacts if r.get("memory_used", False))
    retried        = sum(1 for r in artifacts if (r.get("num_attempts") or 1) > 1)
    recovered      = sum(
        1 for r in artifacts
        if (r.get("num_attempts") or 1) > 1 and _artifact_success(r)
    )
    attempts_counts = [(r.get("num_attempts") or 1) for r in artifacts]

    # ── initially-failed counters (uses artifact field from closed_loop_runner) ──
    initially_failed_count = sum(1 for r in artifacts if r.get("initially_failed", False))
    recovered_from_initial_failure = sum(
        1 for r in artifacts
        if r.get("initially_failed", False) and _artifact_success(r)
    )

    # ── per-attempt counters ──────────────────────────────────────────────
    all_attempts: list[dict] = [
        a
        for r in artifacts
        for a in (r.get("attempts") or [])
        if isinstance(a, dict)
    ]
    n_attempts = len(all_attempts)

    if n_attempts:
        runtime_error_count = sum(1 for a in all_attempts if a.get("runtime_error", False))
        timeout_count       = sum(1 for a in all_attempts if a.get("timeout", False))
        runtime_error_rate  = round(runtime_error_count / n_attempts, 4)
        timeout_rate        = round(timeout_count / n_attempts, 4)
    else:
        runtime_error_rate = 0.0
        timeout_rate       = 0.0

    # ── failure type distribution (per attempt) ───────────────────────────
    # Priority: timeout > runtime_error > semantic_error > unknown
    # Successful attempts (no classified error, run succeeded) are skipped.
    dist: Counter = Counter({"runtime_error": 0, "semantic_error": 0, "timeout": 0, "unknown": 0})

    for r in artifacts:
        run_attempts = r.get("attempts") or []
        run_success  = _artifact_success(r)

        for i, attempt in enumerate(run_attempts):
            if not isinstance(attempt, dict):
                continue
            is_final = (i == len(run_attempts) - 1)

            if attempt.get("timeout", False):
                dist["timeout"] += 1
            elif attempt.get("runtime_error", False):
                dist["runtime_error"] += 1
            elif attempt.get("retry_reason") == "semantic_error":
                dist["semantic_error"] += 1
            elif is_final and not run_success:
                # Final attempt of a failed run with no other classified error type
                dist["unknown"] += 1
            # else: successful attempt — not a failure, skip

    return {
        "total_runs":                              total,
        "success_rate":                            round(successes / total, 4),
        "avg_attempts":                            round(mean(attempts_counts), 4),
        "runtime_error_rate":                      runtime_error_rate,
        "timeout_rate":                            timeout_rate,
        "memory_usage_rate":                       round(memory_used / total, 4),
        "retry_trigger_rate":                      round(retried / total, 4),
        "recovery_rate":                            round(recovered / total, 4),  # compat
        "recovery_rate_over_all_tasks":             round(recovered / total, 4),
        "recovery_rate_over_failed_first_attempts": (
            round(recovered_from_initial_failure / initially_failed_count, 4)
            if initially_failed_count > 0 else 0.0
        ),
        "recovery_rate_over_retried_tasks":         round(recovered / retried, 4) if retried > 0 else 0.0,
        "failure_type_distribution": dict(dist),
    }


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------

def render_markdown(metrics: dict) -> str:
    dist   = metrics.get("failure_type_distribution") or {}
    n      = metrics.get("total_runs", 0)

    def pct(v):
        return f"{float(v):.1%}" if n else "—"

    dist_lines = "\n".join(
        f"  - {k}: {v}"
        for k, v in sorted(dist.items())
    ) or "  (none recorded)"

    return (
        "# Reliability Report\n\n"
        "## Summary\n\n"
        "| Metric | Value |\n"
        "|---|---|\n"
        f"| Total Runs | {n} |\n"
        f"| Success Rate | {pct(metrics.get('success_rate', 0))} |\n"
        f"| Avg Attempts | {float(metrics.get('avg_attempts', 0)):.2f} |\n"
        f"| Runtime Error Rate | {pct(metrics.get('runtime_error_rate', 0))} |\n"
        f"| Timeout Rate | {pct(metrics.get('timeout_rate', 0))} |\n"
        f"| Memory Usage Rate | {pct(metrics.get('memory_usage_rate', 0))} |\n"
        f"| Retry Trigger Rate | {pct(metrics.get('retry_trigger_rate', 0))} |\n"
        f"| Recovery Rate | {pct(metrics.get('recovery_rate', 0))} |\n"
        "\n"
        "## Failure Type Distribution\n\n"
        f"{dist_lines}\n"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def generate_report(runs_dir=None, reports_dir=None) -> dict:
    """
    Load artifacts → compute metrics → write JSON + Markdown.
    Returns the metrics dict. Never raises.
    """
    target_runs    = Path(runs_dir)    if runs_dir    else _DEFAULT_RUNS_DIR
    target_reports = Path(reports_dir) if reports_dir else _DEFAULT_REPORTS_DIR

    artifacts = load_artifacts(target_runs)
    metrics   = compute_metrics(artifacts)

    try:
        target_reports.mkdir(parents=True, exist_ok=True)

        json_path = target_reports / "reliability_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        print(f"[Report] JSON  → {json_path}")

        md_path = target_reports / "reliability_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(render_markdown(metrics))
        print(f"[Report] MD    → {md_path}")

    except Exception as e:
        print(f"[Report] WARNING: failed to write reports: {e}")

    return metrics


if __name__ == "__main__":
    result = generate_report()
    print(json.dumps(result, indent=2))
