from evalforge.tasks.base_task import BaseTask
from evalforge.tasks.task_registry import register_task
from evalforge.metrics.metric_registry import get_metric


@register_task
class RecognitionTask(BaseTask):

    name = "recognition"

    primary_metric = "edit_distance"

    def evaluate_primary(self, sample):

        metric_fn = get_metric(self.primary_metric)

        gt = sample["gt"]
        pred = sample["pred"]

        return metric_fn(gt, pred)

    def evaluate_secondary(self, sample):

        invalid = detect_invalid_output(sample["pred"])

        return {
            "invalid_output": invalid
        }

    def map_to_risk_inputs(self, primary_score, secondary_results):

        invalid = secondary_results.get("invalid_output")

        return {
            "performance_drop": primary_score,
            "invalid_rate": 1.0 if invalid else 0.0,
            "severe_error_rate": 0.0,
            "instability": 0.0
        }