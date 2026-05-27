import difflib
import html


def make_html_diff(gt, pred):
    """
    生成 HTML diff
    """
    gt_lines = gt.splitlines()
    pred_lines = pred.splitlines()

    diff = difflib.HtmlDiff(wrapcolumn=80)

    table = diff.make_table(
        gt_lines,
        pred_lines,
        fromdesc="GT",
        todesc="Prediction",
        context=True,
        numlines=2
    )

    return table


def safe_text(text):
    """
    防止 HTML 转义问题
    """
    return html.escape(text[:4000])