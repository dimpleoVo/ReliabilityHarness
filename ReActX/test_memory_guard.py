"""
Minimal test for filter_relevant_memories.
No LLM, no Docker, no Chroma.
"""
from app.loop.closed_loop_runner import filter_relevant_memories

MEMORIES = [
    {
        "task": "print zero",
        "fixed_code": "print(0)",
        "fixed_output": "0\n",
        "bad_code": "print(1/0)",
        "stderr": "ZeroDivisionError",
    }
]

# ── Case 1: task mentions 42, memory fixed_output is "0\n" → should be filtered ──
result = filter_relevant_memories("Write Python code that prints 42.", MEMORIES)
assert result == [], (
    f"expected empty list after filtering, got {result}"
)

# ── Case 2: task has no explicit number → memory should be preserved ──
result2 = filter_relevant_memories("Fix division by zero bug", MEMORIES)
assert result2 == MEMORIES, (
    f"expected memories to be preserved, got {result2}"
)

print("[TEST PASS] memory guard filtered irrelevant memories correctly")
