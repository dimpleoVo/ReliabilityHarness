import html
from difflib import SequenceMatcher

def _escape(s: str) -> str:
    return html.escape(s or "")

def render_inline_diff_html(a: str, b: str, mode: str = "char") -> str:
    a = a or ""
    b = b or ""
    if mode == "word":
        a_seq = a.split()
        b_seq = b.split()
        joiner = " "
    else:
        a_seq = list(a)
        b_seq = list(b)
        joiner = ""

    sm = SequenceMatcher(a=a_seq, b=b_seq)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            out.append(_escape(joiner.join(a_seq[i1:i2])))
        elif tag == "delete":
            out.append(f"<span class='del'>{_escape(joiner.join(a_seq[i1:i2]))}</span>")
        elif tag == "insert":
            out.append(f"<span class='ins'>{_escape(joiner.join(b_seq[j1:j2]))}</span>")
        elif tag == "replace":
            out.append(f"<span class='del'>{_escape(joiner.join(a_seq[i1:i2]))}</span>")
            out.append(f"<span class='ins'>{_escape(joiner.join(b_seq[j1:j2]))}</span>")
    return "".join(out)