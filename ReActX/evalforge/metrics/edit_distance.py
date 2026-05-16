from difflib import SequenceMatcher
from evalforge.metrics.metric_registry import register_metric


@register_metric("edit_distance")
def normalized_edit_distance(gt, pred):
    """
    归一化编辑距离（越大越差）
    使用标准库 difflib，避免额外依赖 Levenshtein
    """
    gt = gt or ""
    pred = pred or ""

    sm = SequenceMatcher(None, gt, pred)
    return 1 - sm.ratio()