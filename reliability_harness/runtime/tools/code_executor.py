from reliability_harness.core.engine import ELE_Service
from reliability_harness.core.llm import llm_service


def clean_error(stderr: str):
    if not stderr:
        return ""
    lines = stderr.strip().split("\n")
    return lines[-1]


class CodeExecutionTool:
    def __init__(self):
        self.engine = ELE_Service({}, llm_client=llm_service)

    def run(self, query: str):
        result = self.engine.run(query)

        # 🔥 统一 stdout / stderr
        stdout = (result.get("stdout") or result.get("output") or "").strip()
        stderr = (result.get("stderr") or "").strip()

        # 🔥 统一 return_code
        if "return_code" in result:
            return_code = result["return_code"]
        else:
            return_code = 0 if result.get("status") == "success" else 1

        is_success = (return_code == 0)

        # fallback：防止无输出
        if is_success and not stdout:
            stdout = "[NO OUTPUT]"

        # 🔥 error 逻辑修正
        if not is_success:
            error_msg = result.get("error") or clean_error(stderr) or "Execution failed"
        else:
            error_msg = None

        sandbox_payload = {
            **result,
            "stdout": stdout,
            "stderr": stderr,
            "return_code": return_code,
            "runtime_error": not is_success,   # 🔥关键
        }

        if is_success:
            return {
                "result": stdout,
                "error": None,
                "generated_code": result.get("generated_code"),
                "raw_llm_response": result.get("raw_llm_response"),
                "sandbox": sandbox_payload,
            }

        return {
            "result": stdout,
            "error": error_msg,
            "generated_code": result.get("generated_code"),
            "raw_llm_response": result.get("raw_llm_response"),
            "sandbox": sandbox_payload,
        }