_RUNTIME_EXCEPTION_NAMES = (
    "Traceback",
    "ZeroDivisionError", "ValueError", "TypeError", "NameError",
    "AttributeError", "IndexError", "KeyError", "ImportError",
    "RuntimeError", "AssertionError", "OverflowError",
)

_SEVERITY_MAP = {
    "sandbox_http_error": "high",
    "timeout": "high",
    "syntax_error": "medium",
    "runtime_exception": "medium",
    "empty_output": "low",
    "observation_mismatch": "low",
    "tool_process_mismatch": "low",
    # reserved
    "memory_pollution": "low",
    "retry_loop": "low",
    "max_retry_exhausted": "high",
}


def classify_runtime_failure(
    traj_dict: dict,
    eval_result: dict | None = None,
    reliability_report: dict | None = None,
) -> dict:
    steps = traj_dict.get("steps") or []
    last_step = steps[-1] if steps else {}
    sandbox = last_step.get("sandbox") or {}

    error = str(last_step.get("error") or "")
    stderr = str(sandbox.get("stderr") or "")
    stdout = str(sandbox.get("stdout") or "")
    observation = str(last_step.get("observation") or "")
    status = last_step.get("status") or ""

    failure_types = []
    evidence = {}

    # sandbox_http_error
    if "Sandbox HTTP" in error:
        failure_types.append("sandbox_http_error")
        evidence["sandbox_http_error"] = error

    # timeout
    if sandbox.get("timeout") or "timeout" in error.lower() or "timeout" in stderr.lower():
        failure_types.append("timeout")
        evidence["timeout"] = error or stderr

    # syntax_error
    if "SyntaxError" in stderr or "SyntaxError" in error:
        failure_types.append("syntax_error")
        evidence["syntax_error"] = stderr or error

    # runtime_exception
    if any(exc in stderr or exc in error for exc in _RUNTIME_EXCEPTION_NAMES):
        if "syntax_error" not in failure_types:  # SyntaxError already covered
            failure_types.append("runtime_exception")
            evidence["runtime_exception"] = stderr or error

    # empty_output
    eval_success = (eval_result or {}).get("runtime_error") is False and status != "error"
    if not stdout and not observation and (status == "error" or not eval_success):
        failure_types.append("empty_output")
        evidence["empty_output"] = "stdout and observation are both empty"

    # observation_mismatch
    if sandbox and observation.strip() != stdout.strip() and (observation or stdout):
        failure_types.append("observation_mismatch")
        evidence["observation_mismatch"] = f"observation={observation!r} stdout={stdout!r}"

    # tool_process_mismatch (from eval failure summary)
    eval_failure = (eval_result or {}).get("failure") or {}
    failure_summary = eval_failure.get("failure_summary") or []
    if any("mismatch" in str(f) for f in failure_summary):
        failure_types.append("tool_process_mismatch")
        evidence["tool_process_mismatch"] = failure_summary

    # max_retry_exhausted
    rr = reliability_report or {}
    if (
        rr.get("success") is False
        and rr.get("retry_triggered") is True
        and (rr.get("attempts") or 0) >= 3
    ):
        failure_types.append("max_retry_exhausted")
        evidence["max_retry_exhausted"] = f"attempts={rr.get('attempts')}, success=False"

    # memory_pollution — reserved, not yet implemented
    # retry_loop — reserved, not yet implemented

    # deduplicate
    failure_types = list(dict.fromkeys(failure_types))

    # severity
    if not failure_types:
        severity = "none"
    else:
        severity_order = {"high": 3, "medium": 2, "low": 1}
        severity = max(
            (_SEVERITY_MAP.get(ft, "low") for ft in failure_types),
            key=lambda s: severity_order.get(s, 0),
        )

    primary = failure_types[0] if failure_types else None

    return {
        "failure_types": failure_types,
        "primary_failure_type": primary,
        "severity": severity,
        "evidence": evidence,
    }
