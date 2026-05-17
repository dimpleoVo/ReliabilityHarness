from app.reasoning.reflection_evaluator import evaluate_reflection


PASSED = 0
FAILED = 0


def check(name, fn):
    global PASSED, FAILED
    try:
        fn()
        PASSED += 1
        print(f"PASS {name}")
    except AssertionError as e:
        FAILED += 1
        print(f"FAIL {name}: {e}")


def test_zero_division_good():
    result = evaluate_reflection(
        reflection="Fix ZeroDivisionError by avoiding division by zero and print a safe value.",
        stderr="ZeroDivisionError: division by zero",
        retry_reason="runtime_error",
        previous_code="print(1 / 0)",
        next_code="print(42)",
    )
    assert result["mentions_root_cause"] is True
    assert result["suggests_actionable_fix"] is True
    assert result["repeats_previous_failure"] is False
    assert result["reflection_quality"] == "good"
    assert result["detected_error_type"] == "ZeroDivisionError"


def test_index_error_good():
    result = evaluate_reflection(
        reflection="Fix IndexError by using index 2 instead of index 3.",
        stderr="IndexError: list index out of range",
        previous_code="print([10, 20, 30][3])",
        next_code="print([10, 20, 30][2])",
    )
    assert result["reflection_quality"] == "good"
    assert result["detected_error_type"] == "IndexError"


def test_timeout_good():
    result = evaluate_reflection(
        reflection="Fix timeout caused by infinite loop; increment the counter.",
        stderr="",
        retry_reason="timeout",
        previous_code="while True:\n    pass",
        next_code="for i in range(5):\n    print(i)",
    )
    assert result["mentions_root_cause"] is True
    assert result["suggests_actionable_fix"] is True
    assert result["reflection_quality"] == "good"
    assert result["detected_error_type"] == "Timeout"


def test_vague_reflection_poor():
    result = evaluate_reflection(reflection="try again")
    assert result["mentions_root_cause"] is False
    assert result["suggests_actionable_fix"] is False
    assert result["reflection_quality"] == "poor"
    assert result["detected_error_type"] == "Unknown"


def test_actionable_partial():
    result = evaluate_reflection(reflection="Change the code and print the final result.")
    assert result["mentions_root_cause"] is False
    assert result["suggests_actionable_fix"] is True
    assert result["reflection_quality"] == "partial"


def test_root_cause_partial():
    result = evaluate_reflection(
        reflection="This failed because of a KeyError.",
        stderr="KeyError: 'score'",
    )
    assert result["mentions_root_cause"] is True
    assert result["suggests_actionable_fix"] is False
    assert result["reflection_quality"] == "partial"
    assert result["detected_error_type"] == "KeyError"


def test_repeated_same_code():
    result = evaluate_reflection(
        reflection="Fix ZeroDivisionError by avoiding division by zero.",
        stderr="ZeroDivisionError: division by zero",
        previous_code="print(1 / 0)",
        next_code="print(1 / 0)",
    )
    assert result["repeats_previous_failure"] is True
    assert result["reflection_quality"] == "poor"


def test_repeated_failure_pattern():
    result = evaluate_reflection(
        reflection="Fix timeout by changing the loop.",
        retry_reason="timeout",
        previous_code="for i in range(3): print(i)",
        next_code="while True:\n    pass",
    )
    assert result["repeats_previous_failure"] is True
    assert result["reflection_quality"] == "poor"


def test_missing_fields():
    result = evaluate_reflection(reflection=None, stderr=None, retry_reason=None)
    assert result["mentions_root_cause"] is False
    assert result["suggests_actionable_fix"] is False
    assert result["repeats_previous_failure"] is False
    assert result["reflection_quality"] == "poor"
    assert result["detected_error_type"] == "Unknown"


def test_error_type_priority():
    result = evaluate_reflection(
        reflection="Fix ZeroDivisionError.",
        stderr="NameError: name 'math' is not defined",
        retry_reason="timeout",
    )
    assert result["detected_error_type"] == "NameError"
    assert result["mentions_root_cause"] is False


def main():
    tests = [
        ("test_zero_division_good", test_zero_division_good),
        ("test_index_error_good", test_index_error_good),
        ("test_timeout_good", test_timeout_good),
        ("test_vague_reflection_poor", test_vague_reflection_poor),
        ("test_actionable_partial", test_actionable_partial),
        ("test_root_cause_partial", test_root_cause_partial),
        ("test_repeated_same_code", test_repeated_same_code),
        ("test_repeated_failure_pattern", test_repeated_failure_pattern),
        ("test_missing_fields", test_missing_fields),
        ("test_error_type_priority", test_error_type_priority),
    ]

    for name, fn in tests:
        check(name, fn)

    print(f"{PASSED} passed, {FAILED} failed")
    if FAILED:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
