def replay_trace(result: dict) -> str:
    lines = []

    trajectory = result.get("trajectory") or []
    events = result.get("reliability_events") or []
    report = result.get("reliability_report") or {}
    tool_reliability = result.get("tool_reliability") or {}
    retry_effectiveness = result.get("retry_effectiveness") or {}
    coding_metrics = result.get("coding_metrics") or {}
    tool_process_reliability = result.get("tool_process_reliability") or {}
    failure_taxonomy = result.get("failure_taxonomy") or {}

    lines.append("=" * 60)
    lines.append("TRACE REPLAY")
    lines.append("=" * 60)

    # ── Reliability Summary ──
    lines.append("\n[Reliability Summary]")
    lines.append(f"  task         : {report.get('task', '')}")
    lines.append(f"  success      : {report.get('success')}")
    lines.append(f"  attempts     : {report.get('attempts')}")
    lines.append(f"  final_score  : {report.get('final_score')}")
    lines.append(f"  error_type   : {report.get('error_type')}")
    lines.append(f"  runtime_error: {report.get('runtime_error')}")
    lines.append(f"  used_memory  : {report.get('used_memory')}")
    lines.append(f"  retry_triggered: {report.get('retry_triggered')}")
    lines.append(f"  score_before : {report.get('score_before')}")
    lines.append(f"  score_after  : {report.get('score_after')}")

    # ── Attempt Timeline ──
    lines.append("\n[Attempt Timeline]")
    for entry in trajectory:
        attempt_num = entry.get("step", "?")
        traj = entry.get("traj") or {}
        ev = entry.get("eval") or {}
        lines.append(
            f"  Attempt {attempt_num}: score={ev.get('score')} "
            f"runtime_error={ev.get('runtime_error')} "
            f"source={ev.get('source', '')}"
        )

    # ── Step Details ──
    lines.append("\n[Step Details]")
    for entry in trajectory:
        attempt_num = entry.get("step", "?")
        traj = entry.get("traj") or {}
        steps = traj.get("steps") or []

        for i, step in enumerate(steps):
            lines.append(f"\n  Attempt {attempt_num} / Step {i + 1}")
            lines.append(f"    thought    : {step.get('thought') or ''}")
            lines.append(f"    action     : {step.get('action') or ''}")
            lines.append(f"    tool       : {step.get('tool') or ''}")
            lines.append(f"    status     : {step.get('status') or ''}")
            lines.append(f"    error      : {step.get('error')}")
            lines.append(f"    latency    : {step.get('latency')}")
            lines.append(f"    observation: {step.get('observation') or ''}")

            lines.append(f"\n  [Generated Code]")
            code = step.get("generated_code") or ""
            for code_line in (code.splitlines() or [""]):
                lines.append(f"    {code_line}")

            sandbox = step.get("sandbox") or {}
            lines.append(f"\n  [Sandbox Result]")
            lines.append(f"    runtime_error: {sandbox.get('runtime_error')}")
            lines.append(f"    stdout : {sandbox.get('stdout') or ''}")
            lines.append(f"    stderr : {sandbox.get('stderr') or ''}")

    # ── Reliability Events ──
    lines.append("\n[Reliability Events]")
    if events:
        for e in events:
            details = e.get("details") or {}
            lines.append(
                f"  [{e.get('stage', '')}] {e.get('event', '')} "
                f"status={e.get('status', '')} details={details}"
            )
    else:
        lines.append("  (no events recorded)")

    # ── Tool Reliability ──
    lines.append("\n[Tool Reliability]")
    if tool_reliability:
        for tool, s in tool_reliability.items():
            lines.append(f"  {tool}:")
            lines.append(f"    total_calls        : {s.get('total_calls')}")
            lines.append(f"    success_calls      : {s.get('success_calls')}")
            lines.append(f"    runtime_error_calls: {s.get('runtime_error_calls')}")
            lines.append(f"    success_rate       : {s.get('success_rate')}")
            lines.append(f"    runtime_error_rate : {s.get('runtime_error_rate')}")
            lines.append(f"    avg_latency        : {s.get('avg_latency')}")
    else:
        lines.append("  (no tool reliability data)")

    # ── Coding Execution Metrics ──
    lines.append("\n[Coding Execution Metrics]")
    if coding_metrics:
        lines.append(f"  execution_success: {coding_metrics.get('execution_success')}")
        lines.append(f"  runtime_error    : {coding_metrics.get('runtime_error')}")
        lines.append(f"  return_code      : {coding_metrics.get('return_code')}")
        lines.append(f"  stdout_match     : {coding_metrics.get('stdout_match')}")
        lines.append(f"  expected_output  : {coding_metrics.get('expected_output')}")
    else:
        lines.append("  (no coding execution metrics)")

    # ── Retry Effectiveness ──
    lines.append("\n[Retry Effectiveness]")
    if retry_effectiveness:
        lines.append(f"  retry_triggered      : {retry_effectiveness.get('retry_triggered')}")
        lines.append(f"  attempts             : {retry_effectiveness.get('attempts')}")
        lines.append(f"  score_before         : {retry_effectiveness.get('score_before')}")
        lines.append(f"  score_after          : {retry_effectiveness.get('score_after')}")
        lines.append(f"  score_delta          : {retry_effectiveness.get('score_delta')}")
        lines.append(f"  improved             : {retry_effectiveness.get('improved')}")
        lines.append(f"  recovered_from_failure: {retry_effectiveness.get('recovered_from_failure')}")
    else:
        lines.append("  (no retry effectiveness data)")

    # ── Tool Process Reliability ──
    lines.append("\n[Tool Process Reliability]")
    if tool_process_reliability:
        lines.append(f"  total_steps              : {tool_process_reliability.get('total_steps')}")
        lines.append(f"  reliable_steps           : {tool_process_reliability.get('reliable_steps')}")
        lines.append(f"  unreliable_steps         : {tool_process_reliability.get('unreliable_steps')}")
        lines.append(f"  process_reliability_score: {tool_process_reliability.get('process_reliability_score')}")
        issues = tool_process_reliability.get("issues") or []
        if issues:
            lines.append("  issues:")
            for issue in issues:
                lines.append(
                    f"    [step {issue.get('step_index')}] "
                    f"{issue.get('issue_type')}: {issue.get('message')}"
                )
        else:
            lines.append("  issues: none")
    else:
        lines.append("  (no tool process reliability data)")

    # ── Failure Taxonomy ──
    lines.append("\n[Failure Taxonomy]")
    if failure_taxonomy:
        lines.append(f"  primary_failure_type: {failure_taxonomy.get('primary_failure_type')}")
        lines.append(f"  severity            : {failure_taxonomy.get('severity')}")
        lines.append(f"  failure_types       : {failure_taxonomy.get('failure_types') or []}")
        evidence = failure_taxonomy.get("evidence") or {}
        if evidence:
            lines.append("  evidence:")
            for k, v in evidence.items():
                lines.append(f"    {k}: {v!r}")
        else:
            lines.append("  evidence: none")
    else:
        lines.append("  (no failure taxonomy data)")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)
