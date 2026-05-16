from evalforge.tasks.base_task import BaseTask


class DetectionTask(BaseTask):

    name = "detection"

    def evaluate_primary(self, sample):

        gt_boxes = sample["gt"]
        pred_boxes = sample["pred"]

        # 简化版 IoU/F1 placeholder
        if not pred_boxes:
            return 1.0

        return 0.3

    def evaluate_secondary(self, sample):

        pred_boxes = sample["pred"]

        miss = len(pred_boxes) == 0

        return {
            "miss_detection": miss
        }

    def map_to_risk_inputs(self, primary_score, secondary_results):

        miss = secondary_results.get("miss_detection")

        return {
            "performance_drop": primary_score,
            "invalid_rate": 1.0 if miss else 0.0,
            "severe_error_rate": 0.0,
            "instability": 0.0
        }