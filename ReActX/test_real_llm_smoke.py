"""
Real LLM smoke test: DeepSeek → code generation → sandbox execution.
Placed in OPTIONAL_TESTS — not run by default.

Run:
    DEEPSEEK_API_KEY=<key> python test_real_llm_smoke.py
    DEEPSEEK_API_KEY=<key> SANDBOX_URL=http://sandbox:9000 python test_real_llm_smoke.py
"""
import os
import sys

# ── Guard: API key ──
if not os.environ.get("DEEPSEEK_API_KEY"):
    print("[SKIP] DEEPSEEK_API_KEY not set")
    sys.exit(0)

sandbox_url = os.environ.get("SANDBOX_URL", "http://localhost:9000")

from app.core.llm import LLM_Engine
from app.core.code_sanitizer import CodeSanitizer
from app.sandbox_client import SandboxClient

TASK = "Write Python code that prints 42."

# ── Step 1: generate code via real DeepSeek ──
try:
    llm = LLM_Engine()
except ValueError as e:
    print(f"[SKIP] LLM init failed: {e}")
    sys.exit(0)

sys_prompt = (
    "You are a Python code generator. "
    "ONLY return valid Python code wrapped in ```python ... ```. "
    "The code MUST use print() to output the result."
)
llm_result = llm.chat(prompt=TASK, system_prompt=sys_prompt)

if not llm_result or not llm_result.get("ok"):
    print(f"[SKIP] LLM call failed: {llm_result}")
    sys.exit(0)

raw = llm_result["content"]
code = CodeSanitizer.sanitize(raw)
if not code:
    code = CodeSanitizer.ensure_print(CodeSanitizer.filter_code_lines(raw.strip()))

assert code, f"LLM returned no extractable code. raw={raw!r}"
print(f"[LLM] generated_code:\n{code}")

# ── Step 2: execute via sandbox ──
client = SandboxClient(base_url=sandbox_url)

try:
    result = client.execute_python(code)
except Exception as e:
    print(f"[SKIP] sandbox service not available at {sandbox_url}: {e}")
    sys.exit(0)

return_code = result.get("return_code", 0 if result.get("status") == "success" else 1)
runtime_error = return_code != 0
stdout = result.get("stdout") or result.get("output") or ""

print(f"[Sandbox] return_code={return_code} stdout={stdout!r}")

assert not runtime_error, f"expected runtime_error=False, got True | result={result}"
assert return_code == 0, f"expected return_code=0, got {return_code} | result={result}"
assert "42" in str(stdout), f"expected '42' in stdout, got {stdout!r} | result={result}"

print("[TEST PASS] real LLM smoke test passed")
