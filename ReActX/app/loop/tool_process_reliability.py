def check_tool_process_reliability(traj_dict: dict) -> dict:
    steps = traj_dict.get("steps") or []
    issues = []
    reliable_steps = 0

    for i, step in enumerate(steps):
        sandbox = step.get("sandbox") or {}
        step_issues = []

        if not step.get("tool"):
            step_issues.append({"step_index": i, "issue_type": "missing_tool", "message": "step.tool is absent"})
        if not step.get("tool_input"):
            step_issues.append({"step_index": i, "issue_type": "missing_tool_input", "message": "step.tool_input is absent"})
        if not step.get("observation"):
            step_issues.append({"step_index": i, "issue_type": "missing_observation", "message": "step.observation is absent"})
        if not step.get("generated_code"):
            step_issues.append({"step_index": i, "issue_type": "missing_generated_code", "message": "step.generated_code is absent"})
        if not step.get("sandbox"):
            step_issues.append({"step_index": i, "issue_type": "missing_sandbox", "message": "step.sandbox is absent"})

        observation = (step.get("observation") or "").strip()
        stdout = (sandbox.get("stdout") or "").strip()
        if sandbox and observation != stdout:
            step_issues.append({
                "step_index": i,
                "issue_type": "observation_mismatch",
                "message": f"observation {observation!r} != sandbox.stdout {stdout!r}",
            })

        runtime_error = sandbox.get("runtime_error", False)
        status = step.get("status") or ""
        if runtime_error and status != "error":
            step_issues.append({
                "step_index": i,
                "issue_type": "runtime_error_status_mismatch",
                "message": f"sandbox.runtime_error=True but step.status={status!r}",
            })
        elif not runtime_error and status != "success" and status:
            step_issues.append({
                "step_index": i,
                "issue_type": "runtime_error_status_mismatch",
                "message": f"sandbox.runtime_error=False but step.status={status!r}",
            })

        if step_issues:
            issues.extend(step_issues)
        else:
            reliable_steps += 1

    total = len(steps)
    unreliable = total - reliable_steps
    score = round(reliable_steps / total, 3) if total else 1.0

    return {
        "total_steps": total,
        "reliable_steps": reliable_steps,
        "unreliable_steps": unreliable,
        "process_reliability_score": score,
        "issues": issues,
    }
