import os
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.memory.vector_store import FailureMemoryVectorStore


def local_format_memory_examples(memories: list[dict]) -> str:
    if not memories:
        return ""

    lines = ["=== Similar Past Failure-Fix Examples ==="]
    for i, m in enumerate(memories, 1):
        lines.append(f"\n--- Example {i} ---")
        if m.get("task"):
            lines.append(f"Task: {m['task']}")
        if m.get("bad_code"):
            lines.append(f"Bad Code:\n{m['bad_code']}")
        if m.get("stderr"):
            lines.append(f"Error:\n{m['stderr']}")
        if m.get("bad_output"):
            lines.append(f"Bad Output:\n{m['bad_output']}")
        if m.get("fixed_code"):
            lines.append(f"Fixed Code:\n{m['fixed_code']}")
        if m.get("fixed_output"):
            lines.append(f"Fixed Output:\n{m['fixed_output']}")
        if m.get("score_before") or m.get("score_after"):
            lines.append(
                f"Score: {m.get('score_before', '?')} \u2192 {m.get('score_after', '?')}"
            )
    return "\n".join(lines)


def memory_round_trip():
    item = {
        "task": "similar task minimal memory verification",
        "task_type": "unit",
        "error_type": "runtime_error",
        "bad_code": "print(1 / 0)",
        "bad_output": "",
        "bad_stderr": "ZeroDivisionError: division by zero",
        "fixed_code": "print(0)",
        "fixed_output": "0\n",
        "improved": True,
        "meta": {
            "score_before": 0.0,
            "score_after": 1.0,
        },
    }

    with tempfile.TemporaryDirectory(prefix="reactx_failure_memory_test_") as tmpdir:
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            vector_store = FailureMemoryVectorStore()
            vector_store.add(item)
            retrieved = vector_store.search("similar task", top_k=1)
        finally:
            os.chdir(old_cwd)

    print("\nRETRIEVED_RESULT=")
    print(retrieved)

    assert retrieved, "search() returned no results"

    prompt = local_format_memory_examples(retrieved)
    print("\nMEMORY_PROMPT=")
    print(prompt)

    assert "Fixed Code" in prompt
    assert "Error" in prompt


if __name__ == "__main__":
    memory_round_trip()
