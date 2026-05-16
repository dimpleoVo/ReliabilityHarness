from typing import Dict, Any, List
from evalforge.metrics.metric_registry import get_metric


class Evaluator:
    def __init__(self, metrics: List[str]):
        self.metrics = metrics
        self.metric_fns = {
            name: get_metric(name) for name in metrics
        }

    def evaluate(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        pred = sample.get("prediction")
        gt = sample.get("ground_truth")
        meta = sample.get("meta", {})

        runtime_error = meta.get("has_error", False)

        # 没有GT：不算semantic metric，只保留runtime signal
        if gt is None:
            return {
                "score": None,
                "metrics": {},
                "num_steps": meta.get("num_steps"),
                "runtime_error": runtime_error,
                "no_gt": True,
            }

        results = {}

        for name, fn in self.metric_fns.items():
            try:
                results[name] = fn(gt, pred)
            except Exception:
                results[name] = None

        # 默认主分数用 edit_distance
        main_score = results.get("edit_distance")

        return {
            "score": main_score,
            "metrics": results,
            "num_steps": meta.get("num_steps"),
            "runtime_error": runtime_error,
            "no_gt": False,
        }