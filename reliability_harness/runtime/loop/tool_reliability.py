def compute_tool_reliability(trajectory_all: list) -> dict:
    stats = {}

    for entry in trajectory_all:
        traj = entry.get("traj") or {}
        for step in (traj.get("steps") or []):
            tool = step.get("tool") or "unknown"
            sandbox = step.get("sandbox") or {}

            is_success = step.get("status") == "success"
            is_runtime_error = bool(sandbox.get("runtime_error", False))
            latency = step.get("latency")

            if tool not in stats:
                stats[tool] = {
                    "total_calls": 0,
                    "success_calls": 0,
                    "runtime_error_calls": 0,
                    "_latencies": [],
                }

            s = stats[tool]
            s["total_calls"] += 1
            if is_success:
                s["success_calls"] += 1
            if is_runtime_error:
                s["runtime_error_calls"] += 1
            if latency is not None:
                s["_latencies"].append(latency)

    result = {}
    for tool, s in stats.items():
        total = s["total_calls"]
        latencies = s["_latencies"]
        result[tool] = {
            "total_calls": total,
            "success_calls": s["success_calls"],
            "runtime_error_calls": s["runtime_error_calls"],
            "success_rate": round(s["success_calls"] / total, 3) if total else 0.0,
            "runtime_error_rate": round(s["runtime_error_calls"] / total, 3) if total else 0.0,
            "avg_latency": round(sum(latencies) / len(latencies), 3) if latencies else None,
        }

    return result
