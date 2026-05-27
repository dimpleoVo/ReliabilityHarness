import os
import time
import requests


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text or "")


def _call_openai_compat(base_url: str, api_key: str, model: str, messages: list, timeout: int = 90) -> str:
    url = base_url.rstrip("/") + "/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def run_openai_compat_model(model_config, gt_dir: str, output_pred_dir: str):
    """
    OpenAI-compatible runner (DeepSeek/Qwen/Gemini-compat if supported).
    Reads input .md files from input_dir (default: gt_dir), calls LLM, writes pred .md to output_pred_dir.
    """

    os.makedirs(output_pred_dir, exist_ok=True)

    base_url = model_config.get("base_url", "").strip()
    model_name = model_config.get("model", "").strip()
    api_key_env = model_config.get("api_key_env", "OPENAI_API_KEY")
    api_key = os.environ.get(api_key_env, "").strip()

    if not base_url or not model_name:
        raise ValueError("openai_compat_runner requires model_config.base_url and model_config.model")

    if not api_key:
        raise ValueError(f"API key not found in env var: {api_key_env}")

    input_dir = os.path.expanduser(model_config.get("input_dir", gt_dir))
    timeout = int(model_config.get("timeout", 90))
    max_files = model_config.get("max_files", None)
    max_chars = int(model_config.get("max_chars", 6000))  # 防止超长文本炸token
    sleep_s = float(model_config.get("sleep_s", 0.0))     # 控制频率

    system_prompt = model_config.get(
        "system_prompt",
        "You are a document transcription engine. Return ONLY the document content.",
    )
    user_prefix = model_config.get(
        "user_prefix",
        "Please output the following document content EXACTLY as plain text. "
        "Do NOT wrap in markdown/code fences. Do NOT add explanations.\n\nDOCUMENT:\n",
    )

    files = [f for f in os.listdir(input_dir) if f.endswith(".md")]
    files.sort()

    if max_files is not None:
        files = files[: int(max_files)]

    for fname in files:
        in_path = os.path.join(input_dir, fname)
        out_path = os.path.join(output_pred_dir, fname)

        doc = _read_text(in_path)
        doc = doc[:max_chars]

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prefix + doc},
        ]

        t0 = time.time()
        try:
            pred = _call_openai_compat(base_url, api_key, model_name, messages, timeout=timeout)
        except Exception as e:
            # 失败就写空，EvalForge 会统计 invalid output
            pred = ""
        t1 = time.time()

        _write_text(out_path, pred)

        if sleep_s > 0:
            time.sleep(sleep_s)