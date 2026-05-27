"""
Pure success-gate predicate for reliability evaluation.

Intentionally has no imports that initialise external resources (LLM, Docker,
memory, code executor). Safe to import in test collection without API keys.
"""


def is_eval_success(eval_result: dict) -> bool:
    """Success gate using explicit outcome fields only. Never uses edit_distance threshold."""
    if eval_result.get("runtime_error"):
        return False

    # Priority 1-3: explicit outcome fields
    for field in ("final_success", "task_success", "test_passed", "tests_passed"):
        val = eval_result.get(field)
        if val is not None:
            return bool(val)

    # LLM judge path: explicit correct flag
    judge = eval_result.get("judge") or {}
    if judge.get("correct") is not None:
        return bool(judge["correct"])

    metrics = eval_result.get("metrics") or {}

    # LLM judge as metric value (0.0–1.0)
    llm_judge = metrics.get("llm_judge")
    if llm_judge is not None:
        return float(llm_judge) >= 0.8

    return False


def is_improved(before_eval: dict, after_eval: dict) -> bool:
    """True only when first attempt failed AND retry attempt succeeded."""
    return (not is_eval_success(before_eval)) and is_eval_success(after_eval)
