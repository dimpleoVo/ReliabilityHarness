"""
Sandbox smoke test: executes print(42) via X_Service (ELE_Service) execution chain.
No LLM — uses a fake llm_client that returns pre-baked code.
"""
import os
import sys

sandbox_url = os.environ.get("SANDBOX_URL", "http://localhost:9000")


class _FakeLLM:
    """Returns pre-baked code so no real LLM is needed."""
    def chat(self, prompt, system_prompt=""):
        return {"ok": True, "content": "```python\nprint(42)\n```"}


from app.core.engine import X_Service

svc = X_Service(task_config={}, llm_client=_FakeLLM())

try:
    result = svc.run("print 42")
except Exception as e:
    print(f"[SKIP] sandbox service not available at {sandbox_url}: {e}")
    sys.exit(0)

if result.get("status") == "error" and "Connection" in str(result.get("error", "")):
    print(f"[SKIP] sandbox service not available at {sandbox_url}: {result.get('error')}")
    sys.exit(0)

print(f"[Sandbox] result: {result}")

generated_code = result.get("generated_code") or ""
stdout = result.get("stdout") or result.get("output") or ""
return_code = result.get("sandbox", {}).get("return_code", 0 if result.get("status") == "success" else 1)
runtime_error = result.get("sandbox", {}).get("runtime_error", result.get("status") != "success")

assert "print" in generated_code, f"expected 'print' in generated_code, got: {generated_code!r}"
assert return_code == 0, f"expected return_code=0, got {return_code}"
assert not runtime_error, f"expected runtime_error=False, got {runtime_error}"
assert "42" in str(stdout), f"expected '42' in stdout, got {stdout!r}"

print("[TEST PASS] sandbox smoke test passed")
