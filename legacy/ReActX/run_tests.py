"""
Unified test runner for ReActX unit / mock tests.
Run: python run_tests.py
Run with optional (Chroma / Sandbox / Real LLM): python run_tests.py --optional
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

TESTS = [
    # eval adapter & trajectory meta
    "test_trajectory_eval_meta.py",
    # reliability report & events
    "test_reliability_report.py",
    "test_reliability_events.py",
    "test_closed_loop_reliability_events.py",
    # runtime error propagation
    "test_runtime_error_eval_result.py",
    # dataset loader
    "test_dataset_loader_path.py",
    # trace replay
    "test_trace_replay.py",
    # tool reliability
    "test_tool_reliability.py",
    "test_closed_loop_tool_reliability.py",
    # tool process reliability
    "test_tool_process_reliability.py",
    "test_closed_loop_tool_process_reliability.py",
    # retry effectiveness
    "test_retry_effectiveness.py",
    "test_closed_loop_retry_effectiveness.py",
    # coding execution metrics
    "test_coding_metrics.py",
    "test_closed_loop_coding_metrics.py",
    "test_closed_loop_expected_output_metrics.py",
    # failure taxonomy
    "test_failure_taxonomy.py",
    "test_closed_loop_failure_taxonomy.py",
    # memory guard
    "test_memory_guard.py",
]

# Require external services — not run by default
OPTIONAL_TESTS = [
    "test_memory_vector_store.py",              # Chroma + embedding model
    "test_sandbox_smoke.py",                    # sandbox service (SANDBOX_URL)
    "test_real_llm_smoke.py",                   # DeepSeek API (DEEPSEEK_API_KEY) + sandbox
    "test_real_closed_loop_integration.py",     # full integration: LLM + sandbox + closed loop
]

run_optional = "--optional" in sys.argv

all_tests = TESTS + (OPTIONAL_TESTS if run_optional else [])

failed = []

for test_file in all_tests:
    path = HERE / test_file
    print(f"[RUN] {test_file}")
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(HERE),
    )
    if result.returncode == 0:
        print(f"[PASS] {test_file}")
    else:
        print(f"[FAIL] {test_file}")
        failed.append(test_file)
    print()

if failed:
    print(f"[FAILED] {len(failed)} test(s) failed:")
    for f in failed:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("[ALL TESTS PASS]")
