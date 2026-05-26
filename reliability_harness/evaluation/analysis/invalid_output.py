def detect_invalid_output(text):
    t = text.lower().strip()

    if len(t) == 0:
        return "empty_output"

    if "sorry" in t or "can't assist" in t or "cannot assist" in t:
        return "refusal_output"

    if "```markdown" in t:
        return "format_wrapped_output"

    return None