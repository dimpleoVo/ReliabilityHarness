from utils.dataset_loader import get_ground_truth


def classify_task(task: str):
    task = (task or "").lower()

    if "string" in task:
        return "string"
    elif "list" in task:
        return "list"
    elif "fibonacci" in task:
        return "math"
    elif "max" in task:
        return "math"
    elif "print" in task or "python" in task:
        return "code"
    else:
        return "general"


def clean_task(task: str):
    task = task or ""

    # 只提取真正的用户任务部分
    if "Task:" in task:
        task = task.split("Task:")[-1].strip()

    return task.strip()


def trajectory_to_eval_sample(traj_dict):
    pred = (traj_dict.get("final_answer") or "").strip()

    raw_task = traj_dict.get("task", "")
    cleaned_task = clean_task(raw_task)

    steps = traj_dict.get("steps", [])

    gt = get_ground_truth(cleaned_task)

    has_error = any(step.get("status") == "error" for step in steps)

    if gt is None:
        print(f"⚠️ WARNING: GT not found for task: {cleaned_task}")

    _STEP_FIELDS = [
        "thought", "action", "tool", "tool_input",
        "observation", "status", "error", "latency",
        "generated_code", "sandbox",
    ]
    trajectory_steps = [
        {field: (step.get(field) if isinstance(step, dict) else getattr(step, field, None))
         for field in _STEP_FIELDS}
        for step in steps
    ]
    print(f"[EvalAdapter] Attached {len(trajectory_steps)} trajectory step(s) to sample meta")

    return {
        "id": "agent_task_001",
        "steps": traj_dict.get("steps"),
        "prediction": pred,
        "ground_truth": gt,
        "meta": {
            "num_steps": traj_dict.get("num_steps"),
            "has_error": has_error,
            "task_type": classify_task(cleaned_task),
            "doc_type": classify_task(cleaned_task),
            "task": cleaned_task,
            "raw_task": raw_task,
            "no_gt": gt is None,
            "trajectory_steps": trajectory_steps,
        }
    }