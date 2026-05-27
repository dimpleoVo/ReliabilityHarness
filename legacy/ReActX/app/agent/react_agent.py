import time
from app.agent.trajectory import Trajectory, Step


class ReActXAgent:
    def __init__(self, tools):
        self.tools = tools

    def run(self, task: str):
        traj = Trajectory(task)

        thought = f"I need to solve: {task}"
        tool_name = "code_executor"
        tool = self.tools[tool_name]

        start = time.time()

        try:
            result = tool.run(task)

            observation = result.get("result")
            error = result.get("error")
            generated_code = result.get("generated_code")
            sandbox = result.get("sandbox", {})

            status = "success" if error is None else "error"

        except Exception as e:
            observation = None
            error = str(e)
            generated_code = None
            sandbox = {}
            status = "error"
            result = {
                "result": None,
                "error": str(e),
                "generated_code": None,
                "sandbox": {},
            }

        latency = time.time() - start

        step = Step(
            thought=thought,
            action="execute_code",
            tool=tool_name,
            tool_input=task,
            observation=observation,
            status=status,
            error=error,
            latency=latency,
            extra=result,
            generated_code=generated_code,
            sandbox=sandbox,
        )

        traj.add_step(step)
        traj.set_final_answer(observation)

        return traj