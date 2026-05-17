"""
Real LLM + Real Sandbox Closed-Loop Demo
Calls: real LLM (DeepSeek) → real Docker sandbox → real evaluator → real retry/reflection
       → real artifact persistence → real reliability report

Run:
    cd ReActX
    SANDBOX_URL=http://localhost:9000 python demo_real_closed_loop.py
"""
import os
import sys
import requests as _requests

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

# ── fixed scenario ─────────────────────────────────────────────────────────────
TASK            = "Write Python code that prints the number 42."
EXPECTED_OUTPUT = "42"
MAX_ATTEMPTS    = 3
_EDIT_OK        = 0.05  # mirrors closed_loop_runner._EDIT_DISTANCE_OK

RUNS_DIR    = os.path.join(_HERE, "runs")
REPORTS_DIR = os.path.join(_HERE, "reports")

_SYSTEM_PROMPT = (
    "You are a Python code generator. "
    "Output ONLY a single Python code block in ```python ... ``` format. "
    "No explanations. No prose. No comments outside the block. "
    "The code MUST use print() to output the result."
)


# ── pre-flight ─────────────────────────────────────────────────────────────────

def _check_api_key() -> str:
    key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not key:
        print("[ERROR] DEEPSEEK_API_KEY is not set.")
        print("  export DEEPSEEK_API_KEY=<your-key>")
        sys.exit(1)
    return key


def _check_sandbox(url: str) -> None:
    try:
        resp = _requests.get(f"{url}/health", timeout=3)
        resp.raise_for_status()
    except Exception as exc:
        print(f"[ERROR] Sandbox not reachable at {url}: {exc}")
        print("  Start sandbox: cd sandbox && docker-compose up -d")
        sys.exit(1)


# ── prompts ────────────────────────────────────────────────────────────────────

def _first_prompt() -> str:
    return (
        f"Task: {TASK}\n\n"
        "Output ONLY a ```python ... ``` code block."
    )


def _reflection_prompt(code: str, runtime_error: bool, stderr: str, actual: str) -> str:
    if runtime_error:
        return (
            f"The previous code raised a runtime error.\n\n"
            f"Task: {TASK}\n\n"
            f"Previous code:\n{code}\n\n"
            f"Error:\n{stderr}\n\n"
            "Fix the error. Output ONLY a ```python ... ``` code block."
        )
    return (
        f"The previous code produced wrong output.\n\n"
        f"Task: {TASK}\n\n"
        f"Expected output: {EXPECTED_OUTPUT!r}\n"
        f"Actual output  : {actual!r}\n\n"
        f"Previous code:\n{code}\n\n"
        "Fix the logic. Output ONLY a ```python ... ``` code block."
    )


# ── code extraction ────────────────────────────────────────────────────────────

def _extract_code(raw: str) -> str:
    from app.core.code_sanitizer import CodeSanitizer
    code = CodeSanitizer.extract_code(raw)
    if not code:
        code = CodeSanitizer.filter_code_lines(raw)
    if not code:
        code = raw.strip()
    return code


# ── evaluation ─────────────────────────────────────────────────────────────────

def _evaluate(stdout: str, runtime_error: bool) -> dict:
    from app.eval.evaluator import Evaluator
    evaluator = Evaluator(metrics=["edit_distance"])
    sample = {
        "prediction": stdout.strip(),
        "ground_truth": EXPECTED_OUTPUT,
        "meta": {"has_error": runtime_error, "num_steps": 1},
    }
    raw = evaluator.evaluate(sample)
    score = raw.get("metrics", {}).get("edit_distance")
    success = (not runtime_error) and (score is not None) and (score <= _EDIT_OK)
    return {
        "score": score,
        "metrics": raw.get("metrics", {}),
        "runtime_error": runtime_error,
        "source": "edit_distance",
        "success": success,
        "failure": {
            "failure_summary": (
                [] if success
                else (["runtime_error"] if runtime_error else ["semantic_error"])
            )
        },
    }


# ── main ───────────────────────────────────────────────────────────────────────

def run_demo() -> None:
    # ── pre-flight ─────────────────────────────────────────────────────────────
    _check_api_key()
    sandbox_url = (
        os.getenv("SANDBOX_URL")
        or os.getenv("SANDBOX_BASE_URL")
        or "http://localhost:9000"
    )
    _check_sandbox(sandbox_url)

    # ── lazy imports (after pre-flight passes) ─────────────────────────────────
    from app.core.llm import LLM_Engine
    from app.sandbox_client import SandboxClient
    from app.artifacts.run_artifact import save_run_artifact
    from app.reporting.reliability_report import generate_report

    llm     = LLM_Engine()
    sandbox = SandboxClient(base_url=sandbox_url)

    print("=" * 64)
    print("  ReliabilityHarness — Real LLM + Sandbox Closed-Loop Demo")
    print("=" * 64)
    print(f"\n[Config] LLM     : DeepSeek deepseek-chat (REAL)")
    print(f"[Config] Sandbox  : {sandbox_url} (REAL)")
    print(f"[Config] Task     : {TASK!r}")
    print(f"[Config] Expected : {EXPECTED_OUTPUT!r}")
    print(f"[Config] Max tries: {MAX_ATTEMPTS}")

    trajectory_all: list[dict] = []
    success        = False
    current_prompt = _first_prompt()

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\n{'─' * 64}")
        print(f"  Attempt {attempt}/{MAX_ATTEMPTS}")
        print(f"{'─' * 64}")

        # ── LLM ───────────────────────────────────────────────────────────────
        print("[LLM] Calling DeepSeek...")
        llm_resp = llm.chat(current_prompt, system_prompt=_SYSTEM_PROMPT)
        if not llm_resp.get("ok"):
            print(f"[LLM] ERROR: {llm_resp.get('error')}")
            break

        code = _extract_code(llm_resp["content"])
        print(f"\n[Generated Code]\n{code}")

        # ── Sandbox ───────────────────────────────────────────────────────────
        print("\n[Sandbox] Executing...")
        sb = sandbox.execute_python(code, timeout=10)

        stdout        = sb.get("stdout", "").strip()
        stderr        = sb.get("stderr", "").strip()
        runtime_error = sb.get("runtime_error", False)
        timed_out     = sb.get("timeout", False)
        return_code   = sb.get("return_code", 1 if runtime_error else 0)

        print(f"[Sandbox] stdout       : {stdout!r}")
        print(f"[Sandbox] stderr       : {stderr!r}")
        print(f"[Sandbox] runtime_error: {runtime_error}")
        print(f"[Sandbox] timeout      : {timed_out}")

        # ── Evaluator ─────────────────────────────────────────────────────────
        eval_result = _evaluate(stdout, runtime_error)
        score       = eval_result["score"]

        print(f"\n[Eval] edit_distance={score}  success={eval_result['success']}")

        # ── Trajectory entry (matches save_run_artifact schema) ───────────────
        traj_dict = {
            "task": TASK,
            "steps": [{
                "generated_code": code,
                "sandbox": {
                    "stdout":        stdout,
                    "stderr":        stderr,
                    "runtime_error": runtime_error,
                    "timeout":       timed_out,
                    "return_code":   return_code,
                    "runtime":       sb.get("runtime", 0.0),
                },
                "observation": stdout,
                "status": "error" if runtime_error else "success",
            }],
            "final_answer": stdout,
        }

        trajectory_all.append({
            "step":  attempt,
            "input": current_prompt,
            "traj":  traj_dict,
            "eval":  eval_result,
        })

        if eval_result["success"]:
            success = True
            print(f"\n✅ Correct output on attempt {attempt}.")
            break

        if attempt == MAX_ATTEMPTS:
            print(f"\n⏹  Max attempts reached.")
            break

        retry_reason = "runtime_error" if runtime_error else "semantic_error"
        print(f"\n[Reflection] retry_reason={retry_reason}")
        current_prompt = _reflection_prompt(code, runtime_error, stderr, stdout)

    # ── Artifact ───────────────────────────────────────────────────────────────
    final_eval = trajectory_all[-1]["eval"] if trajectory_all else {}
    result_for_artifact = {
        "trajectory": trajectory_all,
        "success":    success,
        "total_steps": len(trajectory_all),
        "reliability_report": {
            "final_score": final_eval.get("score"),
            "used_memory": False,
        },
    }

    print(f"\n{'─' * 64}")
    print("  Artifact")
    print(f"{'─' * 64}")
    artifact_path = save_run_artifact(result_for_artifact, task=TASK, runs_dir=RUNS_DIR)

    # ── Report ─────────────────────────────────────────────────────────────────
    print(f"\n{'─' * 64}")
    print("  Report")
    print(f"{'─' * 64}")
    metrics = generate_report(runs_dir=RUNS_DIR, reports_dir=REPORTS_DIR)

    # ── Summary ────────────────────────────────────────────────────────────────
    rep_abs = os.path.abspath(REPORTS_DIR)
    print(f"\n{'=' * 64}")
    print("  Summary")
    print(f"{'=' * 64}")
    print(f"  Task           : {TASK}")
    print(f"  LLM            : DeepSeek deepseek-chat  [REAL]")
    print(f"  Sandbox        : {sandbox_url}  [REAL]")
    print(f"  Evaluator      : edit_distance  [REAL]")
    print(f"  Num attempts   : {len(trajectory_all)}")
    print(f"  Final success  : {success}")
    print(f"  Artifact       : {artifact_path or '(write failed)'}")
    print(f"  Report (JSON)  : {os.path.join(rep_abs, 'reliability_report.json')}")
    print(f"  Report (MD)    : {os.path.join(rep_abs, 'reliability_report.md')}")
    print(f"  Success rate   : {metrics['success_rate']:.0%}  (cumulative across all runs)")
    print(f"  Recovery rate  : {metrics['recovery_rate']:.0%}  (cumulative across all runs)")
    print(f"{'=' * 64}")

    if success:
        print("\n  ✅ PASS — real closed-loop demo succeeded")
    else:
        print("\n  ❌ FAIL — LLM did not produce correct output within max attempts")


if __name__ == "__main__":
    run_demo()
