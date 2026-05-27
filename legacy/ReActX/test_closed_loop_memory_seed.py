"""
Integration smoke-test: seed one failure-fix memory into the real Chroma
instance, then run the closed loop to confirm retrieval and prompt injection.

Expected log lines (in order):
  [Memory] Retrieved 1 similar failure-fix examples
  [Memory] Injected memory examples into agent prompt

Run inside the Docker container (WORKDIR=/app/ReActX):
  python test_closed_loop_memory_seed.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.memory.vector_store import FailureMemoryVectorStore
from app.loop.closed_loop_runner import run_closed_loop

TASK = "similar task minimal memory verification"

SEED_ITEM = {
    "task": TASK,
    "error_type": "runtime_error",
    "bad_code": "print(1 / 0)",
    "bad_output": "",
    "bad_stderr": "ZeroDivisionError: division by zero",
    "fixed_code": "print(0)",
    "fixed_output": "0\n",
    # task_type / improved not used by add(), but included for completeness
    "task_type": "code",
    "improved": True,
    "meta": {
        "score_before": 0.0,
        "score_after": 1.0,
    },
}


def seed_memory() -> None:
    print("[Seed] Writing test memory entry into Chroma...")
    vs = FailureMemoryVectorStore()
    vs.add(SEED_ITEM)
    print("[Seed] Entry written.")

    # Quick sanity check before running the full loop
    results = vs.search(TASK, top_k=2)
    if not results:
        print("[Seed] WARNING: search() returned nothing immediately after add()")
    else:
        print(f"[Seed] Sanity check passed — search returned {len(results)} result(s)")


def run_integration_test() -> None:
    print(f"\n[Test] Running closed loop for task: {TASK!r}")
    print("[Test] Watch for:")
    print("         [Memory] Retrieved 1 similar failure-fix examples")
    print("         [Memory] Injected memory examples into agent prompt")
    print()

    result = run_closed_loop(TASK)

    print("\n[Test] ── Result ──────────────────────────────")
    print(f"  success            : {result.get('success')}")
    print(f"  reliability_status : {result.get('reliability_status')}")
    print(f"  retry_triggered    : {result.get('retry_triggered')}")
    print(f"  total_steps        : {result.get('total_steps')}")
    print(f"  failure_type       : {result.get('failure_type')}")
    print("[Test] ────────────────────────────────────────")


if __name__ == "__main__":
    seed_memory()
    run_integration_test()
