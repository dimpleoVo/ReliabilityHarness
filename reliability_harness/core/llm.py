import logging
from typing import List, Dict, Any, Optional
import os
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLM_Engine:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")

        if not self.api_key:
            raise ValueError("未找到 API Key！请在 .env 文件中配置 DEEPSEEK_API_KEY。")

        self.base_url = "https://api.deepseek.com"

    # =============================
    # 🔥 轻量 clean（不删字符，只替换危险符号）
    # =============================

    def _fix_unicode_quotes(self, text: str) -> str:
        if not text:
            return ""
        return (
            text
            .replace("\u201c", '"')
            .replace("\u201d", '"')
            .replace("\u2018", "'")
            .replace("\u2019", "'")
            )
    
    def _normalize_text(self, text: str) -> str:
        if not text:
            return ""

        return (
            text
            .replace("“", "\"")
            .replace("”", "\"")
            .replace("‘", "'")
            .replace("’", "'")
            .replace("\u00A0", " ")
            .replace("\u200B", "")
        )

    # =============================
    # 🔥 核心 chat
    # =============================
    def chat(
        self,
        prompt: str,
        system_prompt: str = "你是一个有用的助手。",
        history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:

        try:
            history = history or []
        

            # 👉 保留原始输入（白盒）
            raw_prompt = prompt

            # 👉 只做轻量 normalize（不破坏语义）
            prompt = self._normalize_text(prompt)
            system_prompt = self._normalize_text(system_prompt)

            # =============================
            # 构造 messages
            # =============================
            messages = [{
                "role": "system",
                "content": self._fix_unicode_quotes(system_prompt)
            }]

            for msg in history:
                if msg.get("role") in ["user", "assistant"] and msg.get("content"):
                    messages.append({
                        "role": msg["role"],
                        "content": self._fix_unicode_quotes(str(msg["content"]))
                    })

            messages.append({
                "role": "user",
                "content": prompt
            })

            logger.info(f"Sending request with history ({len(history)} msgs)...")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.1
            }

            # =============================
            # 🔥 核心修复：使用 httpx（彻底解决 encoding）
            # =============================
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )

            if response.status_code != 200:
                return {
                    "ok": False,
                    "content": None,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }

            resp_json = response.json()

            content = resp_json["choices"][0]["message"]["content"]

            content = self._normalize_text(content)

            return {
                "ok": True,
                "content": content,
                "error": None,

                # 🔥 白盒信息（关键）
                "debug": {
                    "llm_input": raw_prompt,
                    "normalized_input": prompt,
                    "messages": messages
                }
            }

        except Exception as e:
            logger.error(f"DeepSeek Chat Error: {e}")

            return {
                "ok": False,
                "content": None,
                "error": str(e)
            }

    # =============================
    # RAG
    # =============================
    def generate(self, query: str, context_chunks: List[str]) -> Dict[str, Any]:
        context_str = "\n".join([f"- {chunk}" for chunk in context_chunks])

        sys_prompt = f"你是一个助手。根据上下文回答。\n上下文:\n{context_str}"

        return self.chat(query, system_prompt=sys_prompt)


# 🔥 必须存在
llm_service = LLM_Engine()

# import logging
# from typing import List, Dict, Any, Optional
# import os
# import requests
# import json

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# os.environ["PYTHONIOENCODING"] = "utf-8"

# class LLM_Engine:
#     def __init__(self):
#         self.api_key = os.getenv("DEEPSEEK_API_KEY")

#         if not self.api_key:
#             raise ValueError("未找到 API Key！请在 .env 文件中配置 DEEPSEEK_API_KEY。")

#         self.base_url = "https://api.deepseek.com"

#     def _clean_text(self, text: str) -> str:
#         if not text:
#             return ""

#         return (
#             text
#             .replace("“", "\"")
#             .replace("”", "\"")
#             .replace("‘", "'")
#             .replace("’", "'")
#         )

#     def chat(
#         self,
#         prompt: str,
#         system_prompt: str = "你是一个有用的助手。",
#         history: Optional[List[Dict]] = None
#     ) -> Dict[str, Any]:

#         try:
#             history = history or []

#             messages = [{
#                 "role": "system",
#                 "content": self._clean_text(system_prompt)
#             }]

#             for msg in history:
#                 if msg.get("role") in ["user", "assistant"] and msg.get("content"):
#                     messages.append({
#                         "role": msg["role"],
#                         "content": self._clean_text(str(msg["content"]))
#                     })

#             messages.append({
#                 "role": "user",
#                 "content": self._clean_text(prompt)
#             })

#             logger.info(f"Sending request with history ({len(history)} msgs)...")

#             headers = {
#                 "Authorization": f"Bearer {self.api_key}",
#                 "Content-Type": "application/json; charset=utf-8"
#             }

#             payload = {
#                 "model": "deepseek-chat",
#                 "messages": messages,
#                 "temperature": 0.1
#             }

#             # 🔥 关键：ASCII-safe（彻底避免编码炸）
#             payload = json.loads(json.dumps(payload, ensure_ascii=True))

#             response = requests.post(
#                 f"{self.base_url}/chat/completions",
#                 headers=headers,
#                 data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
#                 timeout=30
#             )

#             if response.status_code != 200:
#                 return {
#                     "ok": False,
#                     "content": None,
#                     "error": f"HTTP {response.status_code}: {response.text}"
#                 }

#             resp_json = response.json()

#             content = resp_json["choices"][0]["message"]["content"]

#             content = self._clean_text(content)

#             return {
#                 "ok": True,
#                 "content": content,
#                 "error": None
#             }

#         except Exception as e:
#             logger.error(f"DeepSeek Chat Error: {e}")

#             return {
#                 "ok": False,
#                 "content": None,
#                 "error": str(e)
#             }


# llm_service = LLM_Engine()