def compute_coding_execution_metrics(
    traj_dict: dict,
    expected_output: str | None = None,
) -> dict:
    steps = traj_dict.get("steps") or []
    sandbox = (steps[-1].get("sandbox") or {}) if steps else {}

    runtime_error = sandbox.get("runtime_error", False)
    return_code = sandbox.get("return_code", None)
    stdout = sandbox.get("stdout") or ""
    stderr = sandbox.get("stderr") or ""

    execution_success = (not runtime_error) and (return_code == 0)

    if expected_output is None:
        stdout_match = None
    else:
        stdout_match = stdout.strip() == expected_output.strip()

    return {
        "execution_success": execution_success,
        "runtime_error": runtime_error,
        "return_code": return_code,
        "stdout": stdout,
        "stderr": stderr,
        "stdout_match": stdout_match,
        "expected_output": expected_output,
    }
