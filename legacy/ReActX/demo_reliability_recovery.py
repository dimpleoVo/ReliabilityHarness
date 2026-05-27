"""
Demo: Reliability Recovery Pipeline
Deterministic walkthrough: failure → retry → recovery → artifact → report.
No real LLM required. Uses real sandbox if reachable (2s probe), mock otherwise.

Run: cd ReActX && python demo_reliability_recovery.py
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

# ── demo-specific output directories (isolated from production runs/) ──────────
RUNS_DIR    = os.path.join(_HERE, "demo_runs")
REPORTS_DIR = os.path.join(_HERE, "demo_reports")

# ── fixed scenario ─────────────────────────────────────────────────────────────
TASK         = "Write Python code that prints the number 42."
CODE_FAIL    = "print(1 / 0)"    # → ZeroDivisionError
CODE_SUCCESS = "print(42)"       # → stdout "42\n"
REFLECTION   = (
    "Attempt 1 raised ZeroDivisionError: division by zero. "
    "Fix: replace `print(1 / 0)` with `print(42)`."
)


# ── sandbox helpers ────────────────────────────────────────────────────────────

def _sandbox_reachable(base_url: str, timeout: int = 2) -> bool:
    try:
        import requests
        requests.get(f"{base_url}/health", timeout=timeout)
        return True
    except Exception:
        return False


def _run_sandbox(code: str, base_url: str) -> dict:
    from app.sandbox_client import SandboxClient
    return SandboxClient(base_url=base_url).execute_python(code, timeout=10)


def _mock_sandbox(code: str) -> dict:
    if "1 / 0" in code:
        return {
            "status": "error",
            "stdout": "",
            "stderr": (
                "Traceback (most recent call last):\n"
                '  File "<string>", line 1, in <module>\n'
                "ZeroDivisionError: division by zero"
            ),
            "return_code": 1,
            "timeout": False,
            "runtime_error": True,
            "runtime": 0.012,
        }
    return {
        "status": "ok",
        "stdout": "42\n",
        "stderr": "",
        "return_code": 0,
        "timeout": False,
        "runtime_error": False,
        "runtime": 0.009,
    }


# ── trajectory builder ─────────────────────────────────────────────────────────

def _build_entry(step: int, code: str, sandbox_out: dict, reflection: str | None = None) -> dict:
    runtime_error = sandbox_out.get("runtime_error", False)
    success       = not runtime_error and sandbox_out.get("return_code", 1) == 0
    return {
        "step":  step,
        "input": reflection or "",
        "traj": {
            "steps": [{
                "generated_code": code,
                "sandbox": {
                    "stdout":        sandbox_out.get("stdout", ""),
                    "stderr":        sandbox_out.get("stderr", ""),
                    "runtime_error": runtime_error,
                    "timeout":       sandbox_out.get("timeout", False),
                    "return_code":   sandbox_out.get("return_code", 1),
                    "runtime":       sandbox_out.get("runtime", 0.0),
                },
            }],
        },
        "eval": {
            "score":         1.0 if success else None,
            "runtime_error": runtime_error,
            "source":        "demo_exact_match",
            "metrics":       {"exact_match": 1.0 if success else 0.0},
            "failure":       {"failure_summary": [] if success else ["runtime_error"]},
        },
    }


# ── main ───────────────────────────────────────────────────────────────────────

def run_demo() -> None:
    from app.artifacts.run_artifact import save_run_artifact
    from app.reporting.reliability_report import generate_report

    print("=" * 62)
    print("  ReliabilityHarness — Recovery Demo")
    print("=" * 62)

    sandbox_url = (
        os.getenv("SANDBOX_URL")
        or os.getenv("SANDBOX_BASE_URL")
        or "http://localhost:9000"
    )
    use_real = _sandbox_reachable(sandbox_url)
    mode     = "REAL sandbox" if use_real else "MOCK sandbox"
    execute  = (lambda c: _run_sandbox(c, base_url=sandbox_url)) if use_real else _mock_sandbox

    print(f"\n[Config] {mode}")
    print(f"[Config] task = {TASK!r}\n")

    # ── Attempt 1: deliberate failure ──────────────────────────────────────────
    print("─── Attempt 1 ───────────────────────────────────────────────")
    print(f"  code  : {CODE_FAIL}")
    out1  = execute(CODE_FAIL)
    entry1 = _build_entry(step=1, code=CODE_FAIL, sandbox_out=out1)
    label1 = "FAIL  runtime_error" if out1.get("runtime_error") else "PASS"
    print(f"  result: {label1}")
    if out1.get("stderr"):
        print(f"  stderr: {out1['stderr'].strip().splitlines()[-1]}")

    # ── Reflection ─────────────────────────────────────────────────────────────
    print("\n─── Reflection ──────────────────────────────────────────────")
    print(f"  {REFLECTION}")

    # ── Attempt 2: recovery ────────────────────────────────────────────────────
    print("\n─── Attempt 2 ───────────────────────────────────────────────")
    print(f"  code  : {CODE_SUCCESS}")
    out2   = execute(CODE_SUCCESS)
    entry2 = _build_entry(step=2, code=CODE_SUCCESS, sandbox_out=out2, reflection=REFLECTION)
    recovered = not out2.get("runtime_error", True) and out2.get("return_code", 1) == 0
    label2    = "PASS  recovered" if recovered else "FAIL"
    print(f"  result: {label2}")
    if out2.get("stdout"):
        print(f"  stdout: {out2['stdout'].strip()!r}")

    # ── Persist artifact ───────────────────────────────────────────────────────
    result = {
        "trajectory": [entry1, entry2],
        "success":    recovered,
        "total_steps": 2,
        "reliability_report": {
            "final_score": 1.0 if recovered else 0.0,
            "used_memory": False,
        },
    }
    print("\n─── Artifact ────────────────────────────────────────────────")
    artifact_path = save_run_artifact(result, task=TASK, runs_dir=RUNS_DIR)

    # ── Generate report ────────────────────────────────────────────────────────
    print("\n─── Report ──────────────────────────────────────────────────")
    metrics = generate_report(runs_dir=RUNS_DIR, reports_dir=REPORTS_DIR)

    # ── Summary ────────────────────────────────────────────────────────────────
    rep_abs = os.path.abspath(REPORTS_DIR)
    print("\n" + "=" * 62)
    print("  Summary")
    print("=" * 62)
    print(f"  Task          : {TASK}")
    print(f"  Execution     : {mode}")
    print(f"  Attempts      : 2")
    print(f"  Outcome       : {'RECOVERED' if recovered else 'FAILED'}")
    print(f"  Artifact      : {artifact_path or '(write failed)'}")
    print(f"  Report (JSON) : {os.path.join(rep_abs, 'reliability_report.json')}")
    print(f"  Report (MD)   : {os.path.join(rep_abs, 'reliability_report.md')}")
    print(f"  Success rate  : {metrics['success_rate']:.0%}")
    print(f"  Recovery rate : {metrics['recovery_rate']:.0%}")
    print("=" * 62)


if __name__ == "__main__":
    run_demo()
