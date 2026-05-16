import json
from evalforge.analysis.diff_utils import make_html_diff, safe_text


def generate_report(path, report_data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)


def generate_badcase_html(path, badcases):
    html = """
    <html>
    <head>
    <meta charset="UTF-8">
    <title>EvalForge Badcases</title>
    <style>
    body {
        font-family: Arial, sans-serif;
        margin: 40px;
    }
    .case {
        margin-bottom: 80px;
        border-bottom: 2px solid #ddd;
        padding-bottom: 40px;
    }
    pre {
        background: #f6f6f6;
        padding: 12px;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    table.diff {
        font-family: Courier;
        border: medium;
        width: 100%;
        margin-top: 20px;
    }
    .diff_header {
        background-color: #e0e0e0;
    }
    td.diff_header {
        text-align: right;
    }
    .diff_next {
        background-color: #c0c0c0;
    }
    .diff_add {
        background-color: #aaffaa;
    }
    .diff_chg {
        background-color: #ffff77;
    }
    .diff_sub {
        background-color: #ffaaaa;
    }
    </style>
    </head>
    <body>
    <h1>EvalForge Badcases</h1>
    """

    for case in badcases:
        error_type = case.get("error_type", None)
        diff_html = make_html_diff(case["gt"], case["pred"])

        html += f"""
        <div class="case">
            <h2>Sample: {case['id']}</h2>
            <p><b>Edit Distance:</b> {case['metric']}</p>
        """

        if error_type:
            html += f"<p style='color:red;'><b>Error Type:</b> {error_type}</p>"

        html += f"""
            <h3>GT Preview</h3>
            <pre>{safe_text(case['gt'])}</pre>

            <h3>Prediction Preview</h3>
            <pre>{safe_text(case['pred'])}</pre>

            <h3>Diff</h3>
            {diff_html}
        </div>
        """

    html += """
    </body>
    </html>
    """

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)