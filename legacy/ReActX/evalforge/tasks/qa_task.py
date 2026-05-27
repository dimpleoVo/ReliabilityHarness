from evalforge.tasks.base_task import BaseTask
from evalforge.metrics.metric_registry import get_metric


class QATask(BaseTask):

    name = "qa"

    primary_metric = "llm_judge"

    def evaluate_primary(self, sample):

        metric_fn = get_metric(self.primary_metric)

        return metric_fn(sample["gt"], sample["pred"])

    def evaluate_secondary(self, sample):

        pred = sample["pred"]

        refusal = "sorry" in pred.lower()

        return {
            "refusal": refusal
        }

    def map_to_risk_inputs(self, primary_score, secondary_results):

        refusal = secondary_results.get("refusal")

        return {
            "performance_drop": 1 - primary_score,
            "invalid_rate": 1.0 if refusal else 0.0,
            "severe_error_rate": 0.0,
            "instability": 0.0
        }