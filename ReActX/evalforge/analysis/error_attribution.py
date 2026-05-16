import re


def detect_garbled_text(text):
    """
    粗略检测乱码/异常字符堆积。
    """
    if not text:
        return False

    # 常见乱码特征字符
    suspicious_tokens = ["銆", "鈥", "鍙", "锛", "锟", "�"]

    hit = sum(token in text for token in suspicious_tokens)
    if hit >= 1:
        return True

    # 非常粗糙的异常字符比例检测
    weird_chars = re.findall(r"[^\u4e00-\u9fffA-Za-z0-9\s\.\,\!\?\:\;\-\_\(\)\[\]\/\\#\*\|\`\~\'\"]", text)
    if len(text) > 0 and len(weird_chars) / max(len(text), 1) > 0.2:
        return True

    return False


def attribute_error(pred_text, metric, invalid_error_type=None):
    """
    给单条 prediction 做错误归因。
    """
    if invalid_error_type is not None:
        return invalid_error_type

    t = pred_text.strip()

    if len(t) == 0:
        return "empty_output"

    if t.lower().startswith("```markdown") or t.lower().startswith("```"):
        return "format_wrapped_output"

    if detect_garbled_text(t):
        return "garbled_text"

    if metric >= 0.8:
        return "severe_content_mismatch"

    return "normal"