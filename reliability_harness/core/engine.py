from reliability_harness.core.code_sanitizer import CodeSanitizer
from reliability_harness.sandbox.client import SandboxClient
import logging
import uuid

print("🔥 ENGINE FILE:", __file__)


class SimpleConfig:
    def __init__(self, dictionary):
        if not dictionary:
            return
        for key, value in dictionary.items():
            setattr(self, key, value)


class X_Service:
    def __init__(self, task_config: dict, llm_client):
        self.cfg = SimpleConfig(task_config or {})
        self.llm = llm_client
        self.task_id = str(uuid.uuid4())
        self._debug_injected = False

    def _generate_code_with_llm(self, query: str) -> dict:
        sys_prompt = """
You are a Python code generator.

You MUST follow these rules:
- ONLY return valid Python code
- DO NOT return any explanation
- DO NOT repeat the question
- DO NOT include natural language
- ALWAYS wrap code in ```python ... ```
- The code MUST be runnable
- The code MUST use print() to output result
"""

        user_prompt = f"""
Generate Python code for the following task:

{query}

Remember:
- Only return code
- Wrap in ```python ```
"""

        logging.info(f"🤖 Asking LLM to generate code for: {query}")

        llm_result = self.llm.chat(prompt=user_prompt, system_prompt=sys_prompt)

        if not llm_result or not llm_result.get("ok"):
            return {
                "ok": False,
                "code": "",
                "error": llm_result.get("error") if llm_result else "LLM error",
                "raw_response": None,
            }

        raw = llm_result["content"]
        fallback_code = ""
        code = CodeSanitizer.sanitize(raw)

        if not code:
             fallback_code = raw.strip()
             # 再走一次 sanitize（过滤中文等
             fallback_code = CodeSanitizer.filter_code_lines(fallback_code)
             fallback_code = CodeSanitizer.ensure_print(fallback_code)

             if fallback_code:
                 code = fallback_code
             else:
                 return {
                     "ok": False,
                     "code": "",
                     "error": "LLM returned no valid code",
                     "raw_response": raw,
                     }

        return {
            "ok": True,
            "code": code,
            "error": None,
            "raw_response": raw,
        }

    def run(self, query: str) -> dict:
        gen = self._generate_code_with_llm(query)

        if not gen["ok"]:
            return {
                "status": "error",
                "error": gen["error"],
                "generated_code": "",
                "raw_llm_response": gen.get("raw_response"),
                "stdout": "",
                "stderr": "",
                "output": "",
            }

        code = gen["code"]
        

        # # DEBUG 强制第一次犯错误
        # if "hello world" in query and not self._debug_injected:
        #     print("🔥 DEBUG: injecting wrong code")
        #     self._debug_injected = True
        #     code = 'print("helloworld")'
     

        try:
            _client = SandboxClient()
            print(f"[Sandbox] using base_url={_client.base_url}")

            out = _client.execute_python(code, timeout=10)

            stdout = (out.get("stdout") or "").strip()
            stderr = (out.get("stderr") or "").strip()

            if stdout:
                return {
                    "status": "success",
                    "error": None,
                    "generated_code": code,
                    "raw_llm_response": gen["raw_response"],
                    "stdout": stdout,
                    "stderr": stderr,
                    "output": stdout,
                }

            return {
                "status": "error",
                "error": stderr or "Empty output",
                "generated_code": code,
                "raw_llm_response": gen["raw_response"],
                "stdout": stdout,
                "stderr": stderr,
                "output": stdout,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "generated_code": code,
                "raw_llm_response": gen["raw_response"],
                "stdout": "",
                "stderr": str(e),
                "output": "",
            }


# Backward-compatible alias — existing code importing ELE_Service continues to work
ELE_Service = X_Service