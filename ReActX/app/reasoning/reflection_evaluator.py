ERROR_PATTERNS = (
    ("ZeroDivisionError", ("zerodivisionerror", "division by zero")),
    ("IndexError", ("indexerror", "list index out of range")),
    ("KeyError", ("keyerror",)),
    ("NameError", ("nameerror", "not defined")),
    ("Timeout", ("timeout", "infinite loop")),
    ("SemanticError", ("semantic error", "wrong output", "incorrect output")),
)

ACTIONABLE_TERMS = (
    "fix",
    "replace",
    "avoid",
    "change",
    "use",
    "add",
    "remove",
    "import",
    "handle",
    "increment",
    "decrement",
    "correct",
    "print",
)

ACTIONABLE_ERROR_PREFIXES = (
    "fix ",
    "avoid ",
    "handle ",
    "correct ",
    "replace ",
)


def _text(value) -> str:
    return str(value or "")


def _lower(value) -> str:
    return _text(value).lower()


def _detect_error_type_in_text(text: str) -> str:
    haystack = _lower(text)
    for error_type, patterns in ERROR_PATTERNS:
        if any(pattern in haystack for pattern in patterns):
            return error_type
    return "Unknown"


def _detect_error_type(stderr: str, retry_reason: str, reflection: str) -> str:
    for source in (stderr, retry_reason, reflection):
        detected = _detect_error_type_in_text(source)
        if detected != "Unknown":
            return detected
    return "Unknown"


def _mentions_root_cause(reflection: str, stderr: str, retry_reason: str) -> bool:
    reflection_error = _detect_error_type_in_text(reflection)
    if reflection_error == "Unknown":
        return False

    expected_error = _detect_error_type(stderr, retry_reason, "")
    if expected_error == "Unknown":
        return True

    return reflection_error == expected_error


def _suggests_actionable_fix(reflection: str) -> bool:
    haystack = _lower(reflection)
    words = set(haystack.replace(".", " ").replace(",", " ").replace(";", " ").split())
    if words.intersection(ACTIONABLE_TERMS):
        return True
    return any(prefix in haystack for prefix in ACTIONABLE_ERROR_PREFIXES)


def _contains_missing_math_import_pattern(code: str) -> bool:
    haystack = _lower(code)
    return "math.sqrt" in haystack and "import math" not in haystack and "from math import" not in haystack


def _contains_wrong_key_pattern(code: str) -> bool:
    haystack = _lower(code)
    if "{" not in haystack or "[" not in haystack:
        return False
    if "'score'" in haystack and "['score']" not in haystack:
        return True
    if '"score"' in haystack and '["score"]' not in haystack:
        return True
    return False


def _contains_failure_pattern(code: str) -> bool:
    haystack = _lower(code).replace(" ", "")
    raw = _lower(code)
    return (
        "print(1/0)" in haystack
        or "while true" in raw
        or _contains_wrong_key_pattern(code)
        or _contains_missing_math_import_pattern(code)
    )


def _repeats_previous_failure(previous_code: str, next_code: str) -> bool:
    prev = _text(previous_code).strip()
    nxt = _text(next_code).strip()

    if prev and nxt and prev == nxt:
        return True

    if nxt and _contains_failure_pattern(nxt):
        return True

    return False


def _quality(mentions_root_cause: bool, suggests_actionable_fix: bool, repeats_previous_failure: bool) -> str:
    if repeats_previous_failure:
        return "poor"
    if mentions_root_cause and suggests_actionable_fix:
        return "good"
    if mentions_root_cause or suggests_actionable_fix:
        return "partial"
    return "poor"


def evaluate_reflection(
    reflection: str,
    stderr: str = "",
    retry_reason: str = "",
    previous_code: str = "",
    next_code: str = "",
) -> dict:
    mentions_root_cause = _mentions_root_cause(reflection, stderr, retry_reason)
    suggests_actionable_fix = _suggests_actionable_fix(reflection)
    repeats_previous_failure = _repeats_previous_failure(previous_code, next_code)

    return {
        "mentions_root_cause": mentions_root_cause,
        "suggests_actionable_fix": suggests_actionable_fix,
        "repeats_previous_failure": repeats_previous_failure,
        "reflection_quality": _quality(
            mentions_root_cause=mentions_root_cause,
            suggests_actionable_fix=suggests_actionable_fix,
            repeats_previous_failure=repeats_previous_failure,
        ),
        "detected_error_type": _detect_error_type(stderr, retry_reason, reflection),
    }
