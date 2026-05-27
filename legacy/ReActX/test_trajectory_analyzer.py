from app.reasoning.trajectory_analyzer import analyze_trajectory


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


def test_runtime_fix():
    result = analyze_trajectory([
        {
            "attempt_index": 1,
            "stderr": "ZeroDivisionError: division by zero",
            "runtime_error": True,
            "timeout": False,
            "score": 0.0,
            "reflection": "Fix ZeroDivisionError and avoid division by zero.",
            "retry_reason": "runtime_error",
        },
        {
            "attempt_index": 2,
            "stdout": "42",
            "stderr": "",
            "runtime_error": False,
            "timeout": False,
            "score": 1.0,
            "reflection": "",
            "retry_reason": "",
        },
    ])
    assert result["final_success"] is True
    assert result["recovery_type"] == "runtime_fix"
    assert result["trajectory_quality"] == "good"


def test_timeout_fix():
    result = analyze_trajectory([
        {
            "attempt_index": 1,
            "stderr": "timeout",
            "runtime_error": False,
            "timeout": True,
            "score": 0.0,
            "reflection": "Fix timeout caused by infinite loop.",
            "retry_reason": "timeout",
        },
        {
            "attempt_index": 2,
            "stdout": "done",
            "runtime_error": False,
            "timeout": False,
            "score": 1.0,
        },
    ])
    assert result["recovery_type"] == "timeout_fix"
    assert result["reflection_effective"] is True


def test_semantic_fix():
    result = analyze_trajectory([
        {
            "attempt_index": 1,
            "stdout": "0b101010",
            "runtime_error": False,
            "timeout": False,
            "score": 0.0,
            "reflection": "Replace output with binary string without prefix.",
            "retry_reason": "semantic_error",
        },
        {
            "attempt_index": 2,
            "stdout": "101010",
            "runtime_error": False,
            "timeout": False,
            "score": 1.0,
        },
    ])
    assert result["recovery_type"] == "semantic_fix"
    assert result["root_cause_identified"] is True


def test_unrecovered():
    result = analyze_trajectory([
        {
            "attempt_index": 1,
            "stderr": "NameError: name 'math' is not defined",
            "runtime_error": True,
            "timeout": False,
            "score": 0.0,
            "reflection": "Fix NameError.",
            "retry_reason": "runtime_error",
        }
    ])
    assert result["final_success"] is False
    assert result["recovery_type"] == "unrecovered"
    assert result["trajectory_quality"] == "poor"


def test_repeated_failure():
    result = analyze_trajectory([
        {
            "attempt_index": 1,
            "stderr": "IndexError: list index out of range",
            "runtime_error": True,
            "score": 0.0,
            "retry_reason": "runtime_error",
        },
        {
            "attempt_index": 2,
            "stderr": "IndexError: list index out of range",
            "runtime_error": True,
            "score": 0.0,
            "retry_reason": "runtime_error",
        },
    ])
    assert result["repeated_same_failure"] is True
    assert result["trajectory_quality"] == "poor"


def test_reflection_effective():
    result = analyze_trajectory([
        {"attempt_index": 1, "runtime_error": False, "timeout": False, "score": 0.2},
        {"attempt_index": 2, "runtime_error": False, "timeout": False, "score": 0.6},
    ])
    assert result["reflection_effective"] is True


def test_failure_chain():
    result = analyze_trajectory([
        {"attempt_index": 1, "runtime_error": True, "timeout": False, "score": 0.0},
        {"attempt_index": 2, "runtime_error": False, "timeout": True, "score": 0.0},
        {"attempt_index": 3, "runtime_error": False, "timeout": False, "score": 1.0},
    ])
    assert result["failure_chain"] == ["runtime_error", "timeout", "recovered"], result


def test_empty_attempts():
    result = analyze_trajectory([])
    assert result["num_attempts"] == 0
    assert result["failure_chain"] == []
    assert result["recovery_type"] == "unknown"


def test_missing_fields():
    result = analyze_trajectory([{}])
    assert result["num_attempts"] == 1
    assert result["final_success"] is False
    assert result["trajectory_quality"] == "poor"


def main():
    tests = [
        ("test_runtime_fix", test_runtime_fix),
        ("test_timeout_fix", test_timeout_fix),
        ("test_semantic_fix", test_semantic_fix),
        ("test_unrecovered", test_unrecovered),
        ("test_repeated_failure", test_repeated_failure),
        ("test_reflection_effective", test_reflection_effective),
        ("test_failure_chain", test_failure_chain),
        ("test_empty_attempts", test_empty_attempts),
        ("test_missing_fields", test_missing_fields),
    ]

    for name, fn in tests:
        check(name, fn)

    print(f"{PASSED} passed, {FAILED} failed")
    if FAILED:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
