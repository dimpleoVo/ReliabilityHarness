import time
from typing import Any, Dict, Optional


class Step:
    def __init__(
        self,
        thought: str,
        action: str,
        tool: str,
        tool_input: Any,
        observation: Any,
        status: str,
        error: Optional[str] = None,
        latency: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
        generated_code: Optional[str] = None,
        sandbox: Optional[Dict[str, Any]] = None,
    ):
        self.thought = thought
        self.action = action
        self.tool = tool
        self.tool_input = tool_input
        self.observation = observation
        self.status = status
        self.error = error
        self.latency = latency
        self.extra = extra or {}
        self.generated_code = generated_code
        self.sandbox = sandbox or {}

    def to_dict(self):
        return {
            "thought": self.thought,
            "action": self.action,
            "tool": self.tool,
            "tool_input": self.tool_input,
            "observation": self.observation,
            "status": self.status,
            "error": self.error,
            "latency": self.latency,
            "extra": self.extra,
            "generated_code": self.generated_code,
            "sandbox": self.sandbox,
        }


class Trajectory:
    def __init__(self, task: str):
        self.task = task
        self.steps = []
        self.final_answer = None
        self.start_time = time.time()

    def add_step(self, step: Step):
        self.steps.append(step)

    def set_final_answer(self, ans):
        self.final_answer = ans

    def to_dict(self):
        return {
            "task": self.task,
            "steps": [s.to_dict() for s in self.steps],
            "final_answer": self.final_answer,
            "num_steps": len(self.steps),
            "time": time.time() - self.start_time,
        }