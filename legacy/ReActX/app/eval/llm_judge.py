import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"


def llm_judge(task: str, prediction: str):
    if not DEEPSEEK_API_KEY:
        return {
            "correct": False,
            "reason": "missing_deepseek_api_key"
        }

    prompt = f"""
You are an evaluator.

The system is an execution-based agent:
- It generates Python code
- Executes the code
- Returns the execution result (observation)

Your job is to judge whether the FINAL OUTPUT is correct.

Task:
{task}

Final Output:
{prediction}

Rules:
- The output is NOT code, it is execution result
- Judge based on correctness of result, not code format
- Be strict about exact match if needed

Return JSON:
{{
  "correct": true/false,
  "reason": "..."
}}
"""

    resp = requests.post(
        DEEPSEEK_URL,
        headers={
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0
        },
        timeout=60
    )
    resp.raise_for_status()

    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()

    # 兼容 ```json ... ``` 返回
    if content.startswith("```"):
        content = content.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(content)
        return {
            "correct": bool(result.get("correct", False)),
            "reason": str(result.get("reason", ""))
        }
    except Exception:
        return {
            "correct": False,
            "reason": "judge_parse_error",
            "raw": content
        }