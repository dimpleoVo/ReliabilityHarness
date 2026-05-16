import os, json, html
from typing import List, Dict, Any
from evalforge.analysis.diff_html import render_inline_diff_html

def _e(s: str) -> str:
    return html.escape(s or "")

def write_badcase_debugger_html(
    out_path: str,
    badcases: List[Dict[str, Any]],
    title: str = "EvalForge Badcase Visual Debugger",
):
    # 预构建过滤项
    doc_types = sorted({c.get("meta", {}).get("doc_type", "unknown") for c in badcases})
    err_types = sorted({c.get("error_type", "unknown") for c in badcases})

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # HTML
    parts = []
    parts.append(f"<!doctype html><html><head><meta charset='utf-8'><title>{_e(title)}</title>")
    parts.append("""
<style>
body{font-family:Arial;margin:0;display:flex;height:100vh;}
#left{width:320px;border-right:1px solid #ddd;overflow:auto;padding:12px;}
#main{flex:1;overflow:auto;padding:16px;}
.case{padding:8px;border:1px solid #eee;margin:8px 0;border-radius:8px;}
.case:hover{border-color:#bbb;}
.meta{font-size:12px;color:#555;}
.ins{background:#d4fcbc;}
.del{background:#fbb6c2;text-decoration:line-through;}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
pre{white-space:pre-wrap;word-wrap:break-word;padding:10px;border:1px solid #eee;border-radius:8px;}
.badge{display:inline-block;padding:2px 6px;border-radius:999px;background:#f2f2f2;font-size:12px;margin-right:6px;}
select,input{width:100%;padding:8px;margin:6px 0;}
img{max-width:100%;border:1px solid #eee;border-radius:8px;}
hr{border:none;border-top:1px solid #eee;margin:16px 0;}
</style>
<script>
function applyFilters(){
  const q = document.getElementById('q').value.toLowerCase();
  const dt = document.getElementById('doc_type').value;
  const et = document.getElementById('err_type').value;
  document.querySelectorAll('.caseLink').forEach(el=>{
    const cid = el.getAttribute('data-id');
    const doc = el.getAttribute('data-doc');
    const err = el.getAttribute('data-err');
    const text = el.getAttribute('data-text');
    let ok = true;
    if(dt !== 'ALL' && doc !== dt) ok = false;
    if(et !== 'ALL' && err !== et) ok = false;
    if(q && !(cid.includes(q) || text.includes(q))) ok = false;
    el.style.display = ok ? 'block' : 'none';
  });
}
</script>
</head><body>
""")

    # 左侧导航
    parts.append("<div id='left'>")
    parts.append("<h3>Badcases</h3>")
    parts.append("<input id='q' placeholder='Search id/text...' oninput='applyFilters()'/>")
    parts.append("<select id='doc_type' onchange='applyFilters()'><option value='ALL'>All doc_type</option>")
    for x in doc_types:
        parts.append(f"<option value='{_e(x)}'>{_e(x)}</option>")
    parts.append("</select>")
    parts.append("<select id='err_type' onchange='applyFilters()'><option value='ALL'>All error_type</option>")
    for x in err_types:
        parts.append(f"<option value='{_e(x)}'>{_e(x)}</option>")
    parts.append("</select>")
    parts.append("<div class='meta'>Click a case to jump. Diff highlights: <span class='del'>del</span>/<span class='ins'>ins</span></div>")

    for c in badcases:
        cid = str(c.get("id", "unknown")).lower()
        doc = str(c.get("meta", {}).get("doc_type", "unknown"))
        err = str(c.get("error_type", "unknown"))
        text = (c.get("pred","")[:80] + " " + c.get("gt","")[:80]).lower()
        score = c.get("score", c.get("metric", None))
        parts.append(
            f"<a class='caseLink' href='#{_e(cid)}' data-id='{_e(cid)}' data-doc='{_e(doc)}' data-err='{_e(err)}' data-text='{_e(text)}' style='text-decoration:none;color:inherit;'>"
            f"<div class='case'><div><span class='badge'>{_e(doc)}</span><span class='badge'>{_e(err)}</span></div>"
            f"<div class='meta'>id={_e(cid)} | score={_e(str(score))}</div></div></a>"
        )
    parts.append("</div>")  # left

    # 主内容
    parts.append("<div id='main'>")
    parts.append(f"<h2>{_e(title)}</h2>")

    for c in badcases:
        cid = str(c.get("id", "unknown"))
        gt = c.get("gt", "") or ""
        pred = c.get("pred", "") or ""
        meta = c.get("meta", {}) or {}
        doc = meta.get("doc_type", "unknown")
        err = c.get("error_type", "unknown")
        score = c.get("score", "")
        img_path = meta.get("image_path")  # 预留：后续可挂 pdf page 渲染

        parts.append(f"<hr><div id='{_e(cid.lower())}'></div>")
        parts.append(f"<h3>{_e(cid)} <span class='badge'>{_e(doc)}</span> <span class='badge'>{_e(err)}</span> <span class='badge'>score={_e(str(score))}</span></h3>")
        parts.append(f"<div class='meta'>meta={_e(json.dumps(meta, ensure_ascii=False)[:300])}</div>")

        if img_path and os.path.exists(img_path):
            parts.append(f"<div><img src='{_e(img_path)}' alt='page image'></div>")

        diff_char = render_inline_diff_html(gt, pred, mode="char")
        diff_word = render_inline_diff_html(gt, pred, mode="word")

        parts.append("<div class='grid'>")
        parts.append(f"<div><h4>GT</h4><pre>{_e(gt[:6000])}</pre></div>")
        parts.append(f"<div><h4>Pred</h4><pre>{_e(pred[:6000])}</pre></div>")
        parts.append("</div>")

        parts.append("<h4>Diff (char-level)</h4>")
        parts.append(f"<pre>{diff_char}</pre>")
        parts.append("<h4>Diff (word-level)</h4>")
        parts.append(f"<pre>{diff_word}</pre>")

    parts.append("</div></body></html>")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("".join(parts))