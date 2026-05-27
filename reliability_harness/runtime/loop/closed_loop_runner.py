from reliability_harness.runtime.agent.react_agent import ReliabilityHarnessAgent
from reliability_harness.runtime.loop.tool_reliability import compute_tool_reliability
from reliability_harness.runtime.loop.retry_effectiveness import compute_retry_effectiveness
from reliability_harness.runtime.loop.coding_metrics import compute_coding_execution_metrics
from reliability_harness.runtime.loop.tool_process_reliability import check_tool_process_reliability
from reliability_harness.runtime.loop.failure_taxonomy import classify_runtime_failure
from reliability_harness.runtime.tools.code_executor import CodeExecutionTool
from reliability_harness.runtime.loop.eval_adapter import trajectory_to_eval_sample
from reliability_harness.runtime.loop.success_gate import is_eval_success, is_improved
from reliability_harness.utils.dataset_loader import get_ground_truth
from reliability_harness.evaluation.runtime_eval.evaluator import Evaluator
from reliability_harness.evaluation.runtime_eval.failure_analyzer import FailureAnalyzer
from reliability_harness.artifacts.run_artifact import save_run_artifact

# 🔥 memory
from reliability_harness.memory.store import FailureMemoryStore
from reliability_harness.memory.retriever import FailureMemoryRetriever
from reliability_harness.memory.prompt_memory import MemoryPromptBuilder
from reliability_harness.memory.schema import FailureMemoryItem
from reliability_harness.memory.vector_store import FailureMemoryVectorStore

# 🔥 judge
from reliability_harness.evaluation.runtime_eval.llm_judge import llm_judge

failure_analyzer = FailureAnalyzer()


# ===============================
# Memory Retrieval Guard
# ===============================
import re as _re

def _extract_explicit_numbers(text: str) -> set[str]:
    return set(_re.findall(r'\b\d+\b', text or ""))


def filter_relevant_memories(task: str, memories: list[dict]) -> list[dict]:
    task_numbers = _extract_explicit_numbers(task)
    if not task_numbers:
        return memories

    filtered = []
    for m in memories:
        output_numbers = _extract_explicit_numbers(m.get("fixed_output") or "")
        if output_numbers and output_numbers.isdisjoint(task_numbers):
            continue
        filtered.append(m)

    dropped = len(memories) - len(filtered)
    if dropped > 0 and not filtered:
        print("[Memory Guard] filtered all memories due to task-output mismatch")
    elif dropped > 0:
        print(f"[Memory Guard] filtered {dropped} irrelevant memory example(s)")

    return filtered


# ===============================
# 🔥 Memory Prompt Formatter
# ===============================
def format_memory_examples(memories: list[dict]) -> str:
    if not memories:
        return ""
    lines = ["=== Similar Past Failure-Fix Examples ==="]
    for i, m in enumerate(memories, 1):
        lines.append(f"\n--- Example {i} ---")
        if m.get("task"):
            lines.append(f"Task: {m['task']}")
        if m.get("bad_code"):
            lines.append(f"Bad Code:\n{m['bad_code']}")
        if m.get("stderr"):
            lines.append(f"Error:\n{m['stderr']}")
        if m.get("bad_output"):
            lines.append(f"Bad Output:\n{m['bad_output']}")
        if m.get("fixed_code"):
            lines.append(f"Fixed Code:\n{m['fixed_code']}")
        if m.get("fixed_output"):
            lines.append(f"Fixed Output:\n{m['fixed_output']}")
        if m.get("score_before") or m.get("score_after"):
            lines.append(f"Score: {m.get('score_before', '?')} → {m.get('score_after', '?')}")
    return "\n".join(lines)


# ===============================
# 🔥 Reflection Builder（统一用score）
# ===============================
def build_reflection_input(task, traj_dict, eval_result):

    steps = traj_dict.get("steps", [])
    final_answer = traj_dict.get("final_answer", "")

    last_step = steps[-1] if steps else {}

    error = last_step.get("error", "")
    observation = last_step.get("observation", "")
    generated_code = last_step.get("generated_code", "")

    sandbox = last_step.get("sandbox", {})
    stderr = sandbox.get("stderr", "")
    stdout = sandbox.get("stdout", "")


    runtime_error = sandbox.get("runtime_error", False)

    # 🔥 统一用 score
    score = eval_result.get("score")
    no_gt = eval_result.get("no_gt", False)

    # ===== runtime error =====
    if runtime_error:
        return f"""
You are a Python expert.

The following code failed with a runtime error.

Task:
{task}

Previous code:
{generated_code}

Error:
{stderr or error}

Fix the error and return ONLY valid Python code.
"""

    # ===== semantic error =====
    if (not no_gt) and (score is not None) and score > 0:
        return f"""
You are a Python expert.

The code ran but produced incorrect output.

Task:
{task}

Previous code:
{generated_code}

Previous observation:
{observation or stdout or final_answer}

Fix the logic and return ONLY valid Python code.
"""

    return task


# ===============================
# 🔥 ReliabilityHarness evaluation + LLM Judge（核心）
# ===============================
def run_reliability_evaluation(traj_dict):
    print("\n[ReliabilityHarness Eval] evaluating...")

    sample = trajectory_to_eval_sample(traj_dict)

    evaluator = Evaluator(metrics=["edit_distance"])
    eval_raw = evaluator.evaluate(sample)

    failure = failure_analyzer.analyze(sample, eval_raw)

    # ===== 🔥 LLM Judge fallback =====
    if eval_raw.get("no_gt"):
        print("\n🤖 Using LLM Judge...")

        judge = llm_judge(
            task=sample["meta"]["task"],
            prediction=sample["prediction"]
        )

        correct = judge.get("correct", False)

        _steps = traj_dict.get("steps") or []
        _sandbox = (_steps[-1].get("sandbox") or {}) if _steps else {}
        _runtime_error = eval_raw.get("runtime_error", _sandbox.get("runtime_error", False))

        return {
            "score": 0 if correct else 1,
            "metrics": {
                "llm_judge": 1.0 if correct else 0.0
            },
            "num_steps": eval_raw.get("num_steps"),
            "runtime_error": _runtime_error,
            "no_gt": False,
            "failure": failure,
            "judge": judge,
            "source": "llm_judge"
        }

    # ===== GT metric =====
    score = eval_raw.get("metrics", {}).get("edit_distance")

    return {
        "score": score,
        "metrics": eval_raw.get("metrics", {}),
        "num_steps": eval_raw.get("num_steps"),
        "runtime_error": eval_raw.get("runtime_error"),
        "no_gt": eval_raw.get("no_gt", False),
        "failure": failure,
        "source": "reliability_evaluator"
    }


# Deprecated compatibility alias for legacy EvalForge-style calls.
run_evalforge = run_reliability_evaluation


# ===============================
# 🔥 Memory 保存
# ===============================
def save_memory_if_improved(task, trajectory_all, memory_store, vector_store):

    if len(trajectory_all) < 2:
        print("[Memory Gate] saved=False reason=single_step_only")
        return False

    eval1 = trajectory_all[0]["eval"]
    eval2 = trajectory_all[-1]["eval"]

    # Gate 1: first fail → retry success
    if not is_improved(eval1, eval2):
        reason = "first_attempt_success" if is_eval_success(eval1) else "retry_not_success"
        print(f"[Memory Gate] saved=False reason={reason}")
        return False

    # Gate 2: retry sandbox must NOT have runtime_error (read from traj, not eval_result,
    # because the reliability evaluation branch currently hardcodes runtime_error=False in the LLM-judge branch)
    traj2 = trajectory_all[-1]["traj"]
    step2 = traj2["steps"][-1]
    sandbox2 = step2.get("sandbox", {})
    if sandbox2.get("runtime_error", False):
        print("[Memory Gate] saved=False reason=retry_sandbox_runtime_error")
        return False

    traj1 = trajectory_all[0]["traj"]
    step1 = traj1["steps"][-1]
    sandbox1 = step1.get("sandbox", {})

    bad_code = step1.get("generated_code", "")
    bad_output = step1.get("observation", "")
    fixed_code = step2.get("generated_code", "")
    fixed_output = step2.get("observation", "")

    # Gate 3: code or output must differ — guards against judge inconsistency
    # saving identical code as a "failure→fix" pair
    if bad_code == fixed_code and bad_output == fixed_output:
        print("[Memory Gate] saved=False reason=no_code_or_output_change")
        return False

    error_type = "runtime_error" if eval1.get("runtime_error") else "semantic_error"

    item = FailureMemoryItem(
        task=task,
        task_type="code",
        error_type=error_type,
        bad_code=bad_code,
        bad_output=bad_output,
        bad_stderr=sandbox1.get("stderr", ""),
        bad_step=step1,
        fixed_code=fixed_code,
        fixed_output=fixed_output,
        fixed_step=step2,
        improved=True,
        meta={
            "score_before": eval1.get("score"),
            "score_after": eval2.get("score"),
        }
    )

    memory_store.append(item)
    vector_store.add(item.to_dict())

    print("[Memory Gate] saved=True reason=failure_to_success")
    print(item.to_dict())
    return True


# ===============================
# Reliability Event Log
# ===============================
def add_reliability_event(events, stage, event, status="info", details=None):
    events.append({
        "stage": stage,
        "event": event,
        "status": status,
        "details": details or {},
    })


# ===============================
# Reliability Report
# ===============================
def build_reliability_report(
    task,
    success,
    trajectory_all,
    final_eval,
    retry_triggered,
    failure_type,
    retrieved,
    memory_context,
    tool_process_reliability: dict | None = None,
    failure_taxonomy: dict | None = None,
):
    attempts = len(trajectory_all)
    first_entry = trajectory_all[0] if trajectory_all else {}
    first_eval = first_entry.get("eval") or {}
    last_traj = trajectory_all[-1]["traj"] if trajectory_all else {}
    last_steps = last_traj.get("steps", [])

    # Derive initially_failed from stored step_success or from is_eval_success fallback
    first_step_success = first_entry.get("step_success")
    if first_step_success is not None:
        initially_failed = not first_step_success
    else:
        initially_failed = not is_eval_success(first_eval)

    recovery_success = bool(initially_failed and retry_triggered and success)

    tpr = tool_process_reliability or {}
    ftax = failure_taxonomy or {}
    report = {
        "task": task,
        "success": success,  # compat
        "final_success": success,
        "task_success": success,
        "initially_failed": initially_failed,
        "recovery_success": recovery_success,
        "attempts": attempts,
        "final_score": final_eval.get("score"),
        "error_type": failure_type,
        "runtime_error": final_eval.get("runtime_error", False),
        "used_memory": bool(retrieved),
        "memory_examples_count": len(retrieved) if retrieved else 0,
        "retry_triggered": retry_triggered,
        "trajectory_steps": len(last_steps),
        "score_before": first_eval.get("score") if attempts > 1 else None,
        "score_after": final_eval.get("score") if attempts > 1 else None,
        "score_metric": "final_success",
        "score_metric_direction": "higher_is_better",
        "legacy_score_metric": "edit_distance",
        "legacy_score_direction": "lower_is_better",
        "tool_process_reliability_score": tpr.get("process_reliability_score"),
        "tool_process_unreliable_steps": tpr.get("unreliable_steps", 0),
        "tool_process_issue_count": len(tpr.get("issues") or []),
        "primary_failure_type": ftax.get("primary_failure_type"),
        "failure_severity": ftax.get("severity"),
        "failure_type_count": len(ftax.get("failure_types") or []),
    }

    print(
        f"[ReliabilityReport] Built report: success={report['success']}, "
        f"attempts={report['attempts']}, error_type={report['error_type']}"
    )
    return report


# ===============================
# 🔥 Closed Loop（统一score）
# ===============================
def run_closed_loop(task):

    tools = {
        "code_executor": CodeExecutionTool()
    }

    agent = ReliabilityHarnessAgent(tools)

    memory_store = FailureMemoryStore()
    vector_store = FailureMemoryVectorStore()

    try:
        expected_output = get_ground_truth(task)
    except Exception:
        expected_output = None

    max_steps = 3
    trajectory_all = []
    reliability_events = []

    # ===== Memory Retrieval =====
    add_reliability_event(reliability_events, "memory", "memory_search_started", details={"task": task})
    retrieved = vector_store.search(task, top_k=2)
    retrieved = filter_relevant_memories(task, retrieved)
    memory_context = format_memory_examples(retrieved)

    if retrieved:
        add_reliability_event(reliability_events, "memory", "memory_retrieved", details={"count": len(retrieved)})
    else:
        add_reliability_event(reliability_events, "memory", "memory_not_found", status="warn")

    if memory_context:
        print("[Memory] Injected memory examples into agent prompt")
        task_with_memory = f"{task}\n\n{memory_context}"
        add_reliability_event(reliability_events, "memory", "memory_injected", details={"count": len(retrieved)})
    else:
        print("[Memory] No memory injected into agent prompt")
        task_with_memory = task
        add_reliability_event(reliability_events, "memory", "memory_not_injected")

    current_input = f"Solve the task.\n\nTask:\n{task_with_memory}"

    final_answer = None
    coding_metrics = {}
    tool_process_reliability = {}
    failure_taxonomy = {}

    for step in range(1, max_steps + 1):

        print(f"\n===== STEP {step} =====")

        traj = agent.run(current_input)
        traj_dict = traj.to_dict()

        print("\n[Trajectory]")
        print(traj_dict)

        eval_result = run_reliability_evaluation(traj_dict)

        print("\n[Eval Result]")
        print(eval_result)

        step_success = is_eval_success(eval_result)
        is_first_step = (step == 1)

        trajectory_all.append({
            "step": step,
            "input": current_input,
            "traj": traj_dict,
            "eval": eval_result,
            "step_success": step_success,
        })

        final_answer = traj_dict.get("final_answer")
        coding_metrics = compute_coding_execution_metrics(traj_dict, expected_output=expected_output)
        tool_process_reliability = check_tool_process_reliability(traj_dict)
        failure_taxonomy = classify_runtime_failure(traj_dict, eval_result)

        add_reliability_event(
            reliability_events, "eval", "eval_completed",
            status="pass" if step_success else "fail",
            details={"step": step, "success": step_success, "score": eval_result.get("score")},
        )

        if eval_result.get("runtime_error"):
            add_reliability_event(
                reliability_events, "eval", "runtime_error_detected",
                status="error",
                details={"step": step},
            )

        if is_first_step:
            print(f"[Eval Gate] first_success={step_success}")

        # ===== Stop =====
        if step_success:
            print("[Retry Gate] retry_triggered=False")
            print("\n✅ Success, stopping early.")
            add_reliability_event(reliability_events, "loop", "retry_stopped", details={"reason": "success", "step": step})
            break

        if step == max_steps:
            print("[Retry Gate] retry_triggered=False")
            print("\n⏹ Reached max steps.")
            add_reliability_event(reliability_events, "loop", "retry_stopped", details={"reason": "max_steps", "step": step})
            break

        print("[Retry Gate] retry_triggered=True")
        add_reliability_event(reliability_events, "loop", "retry_triggered", details={"step": step})

        reflection_input = build_reflection_input(
            task=task,
            traj_dict=traj_dict,
            eval_result=eval_result
        )

        if memory_context:
            current_input = f"{memory_context}\n\n{reflection_input}"
        else:
            current_input = reflection_input

        print("\n[Reflection Input]")
        print(current_input)

    memory_saved = save_memory_if_improved(task, trajectory_all, memory_store, vector_store)
    add_reliability_event(
        reliability_events, "memory",
        "memory_saved" if memory_saved else "memory_not_saved",
        status="info",
        details={"saved": bool(memory_saved)},
    )

    final_eval = trajectory_all[-1]["eval"] if trajectory_all else {}
    success = is_eval_success(final_eval)
    retry_triggered = len(trajectory_all) > 1

    first_entry_loop = trajectory_all[0] if trajectory_all else {}
    first_step_success_loop = first_entry_loop.get("step_success")
    if first_step_success_loop is not None:
        initially_failed = not first_step_success_loop
    else:
        initially_failed = not is_eval_success(first_entry_loop.get("eval") or {})
    recovery_success = bool(initially_failed and retry_triggered and success)

    if final_eval.get("runtime_error"):
        failure_type = "runtime_error"
    elif not success:
        failure_type = "semantic_error"
    else:
        failure_type = None

    reliability_report = build_reliability_report(
        task=task,
        success=success,
        trajectory_all=trajectory_all,
        final_eval=final_eval,
        retry_triggered=retry_triggered,
        failure_type=failure_type,
        retrieved=retrieved,
        memory_context=memory_context,
        tool_process_reliability=tool_process_reliability,
        failure_taxonomy=failure_taxonomy,
    )

    tool_reliability = compute_tool_reliability(trajectory_all)

    retry_effectiveness = compute_retry_effectiveness(
        trajectory_all=trajectory_all,
        reliability_report=reliability_report,
        metric_name="edit_distance",  # auxiliary score metric only; not a success gate
    )

    # Recompute with reliability_report so max_retry_exhausted can be detected
    final_traj_dict = trajectory_all[-1]["traj"] if trajectory_all else {}
    final_eval_result = trajectory_all[-1]["eval"] if trajectory_all else {}
    failure_taxonomy = classify_runtime_failure(
        final_traj_dict,
        final_eval_result,
        reliability_report=reliability_report,
    )

    result = {
        "trajectory": trajectory_all,
        "final_answer": final_answer,
        "total_steps": len(trajectory_all),
        "success": success,  # compat
        "final_success": success,
        "task_success": success,
        "initially_failed": initially_failed,
        "recovery_success": recovery_success,
        "reliability_status": "pass" if success else "fail",
        "retry_triggered": retry_triggered,
        "failure_type": failure_type,
        "reliability_report": reliability_report,
        "reliability_events": reliability_events,
        "tool_reliability": tool_reliability,
        "retry_effectiveness": retry_effectiveness,
        "coding_metrics": coding_metrics,
        "tool_process_reliability": tool_process_reliability,
        "failure_taxonomy": failure_taxonomy,
    }

    save_run_artifact(result, task=task)

    return result