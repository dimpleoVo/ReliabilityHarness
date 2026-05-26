ROOT_CAUSE_TERMS = (
    "zerodivisionerror",
    "indexerror",
    "keyerror",
    "timeout",
    "infinite loop",
    "nameerror",
    "fix",
    "avoid",
    "replace",
)


def _as_bool(value):
    return bool(value)


def _score(attempt):
    try:
        return float(attempt.get("score") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _text(value):
    return str(value or "").strip()


def _is_success(attempt):
    # Prefer explicit final_success field (avoids score-direction ambiguity)
    if "final_success" in attempt:
        return bool(attempt["final_success"])
    # Legacy fallback: score > 0 assumes higher-is-better normalized score
    return (
        not _as_bool(attempt.get("runtime_error"))
        and not _as_bool(attempt.get("timeout"))
        and _score(attempt) > 0
    )


def _is_failed(attempt):
    return not _is_success(attempt)


def _score_improved(attempts):
    for prev, curr in zip(attempts, attempts[1:]):
        if _score(curr) > _score(prev):
            return True
    return False


def _root_cause_identified(attempts):
    for attempt in attempts:
        reflection = _text(attempt.get("reflection")).lower()
        if any(term in reflection for term in ROOT_CAUSE_TERMS):
            return True
    return False


def _repeated_same_failure(attempts):
    failed = [attempt for attempt in attempts if _is_failed(attempt)]
    if len(failed) < 2:
        return False

    seen_stderr = set()
    seen_retry_reason = set()

    for attempt in failed:
        stderr = _text(attempt.get("stderr"))
        retry_reason = _text(attempt.get("retry_reason"))

        if stderr:
            if stderr in seen_stderr:
                return True
            seen_stderr.add(stderr)

        if retry_reason:
            if retry_reason in seen_retry_reason:
                return True
            seen_retry_reason.add(retry_reason)

    return False


def _reflection_effective(attempts):
    for prev, curr in zip(attempts, attempts[1:]):
        if _is_failed(prev) and _is_success(curr):
            return True
        if _score(curr) > _score(prev):
            return True
    return False


def _recovery_type(attempts, final_success, improved):
    if not attempts or not final_success and not improved:
        return "unrecovered" if attempts else "unknown"

    first = attempts[0]

    if not final_success:
        return "unrecovered"

    if _as_bool(first.get("runtime_error")):
        return "runtime_fix"

    if _as_bool(first.get("timeout")):
        return "timeout_fix"

    if improved and not _as_bool(first.get("runtime_error")):
        return "semantic_fix"

    return "unknown"


def _trajectory_quality(final_success, repeated_same_failure, reflection_effective, improved):
    if final_success and not repeated_same_failure and reflection_effective:
        return "good"
    if improved and not final_success:
        return "partial"
    if repeated_same_failure or (not final_success and not improved):
        return "poor"
    return "partial"


def _attempt_failure_label(attempt):
    if _is_success(attempt):
        return "recovered"
    if _as_bool(attempt.get("timeout")):
        return "timeout"
    if _as_bool(attempt.get("runtime_error")):
        return "runtime_error"

    retry_reason = _text(attempt.get("retry_reason"))
    if retry_reason:
        return retry_reason

    if _score(attempt) <= 0:
        return "semantic_error"

    return "unknown"


def _failure_chain(attempts, final_success):
    if not attempts:
        return []

    chain = [_attempt_failure_label(attempt) for attempt in attempts]
    if final_success and chain[-1] != "recovered":
        chain.append("recovered")
    return chain


def analyze_trajectory(attempts):
    attempts = attempts or []
    num_attempts = len(attempts)

    if not attempts:
        return {
            "num_attempts": 0,
            "final_success": False,
            "root_cause_identified": False,
            "repeated_same_failure": False,
            "reflection_effective": False,
            "recovery_type": "unknown",
            "trajectory_quality": "poor",
            "failure_chain": [],
        }

    final_success = _is_success(attempts[-1])
    improved = _score_improved(attempts)
    repeated_same_failure = _repeated_same_failure(attempts)
    reflection_effective = _reflection_effective(attempts)

    return {
        "num_attempts": num_attempts,
        "final_success": final_success,
        "root_cause_identified": _root_cause_identified(attempts),
        "repeated_same_failure": repeated_same_failure,
        "reflection_effective": reflection_effective,
        "recovery_type": _recovery_type(attempts, final_success, improved),
        "trajectory_quality": _trajectory_quality(
            final_success=final_success,
            repeated_same_failure=repeated_same_failure,
            reflection_effective=reflection_effective,
            improved=improved,
        ),
        "failure_chain": _failure_chain(attempts, final_success),
    }
