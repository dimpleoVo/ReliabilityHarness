from typing import Dict, Any
from reliability_harness.evaluation.analysis.error_patterns import mine_error_patterns
from reliability_harness.evaluation.runtime_eval.boundary_analyzer import BoundaryAnalyzer


class FailureAnalyzer:
    def __init__(self):
        self.history = []
        self.boundary_analyzer = BoundaryAnalyzer()

    def analyze(self, sample: Dict[str, Any], eval_result: Dict[str, Any]) -> Dict[str, Any]:
        pred = sample.get("prediction")
        gt = sample.get("ground_truth")
        meta = sample.get("meta", {})

        steps = meta.get("trajectory_steps") or meta.get("steps", [])
        print(f"[FailureAnalyzer] Loaded {len(steps)} trajectory step(s) from sample meta")

        error_type = self._get_error_type(eval_result)

        result = {
            "prediction": pred,
            "ground_truth": gt,
            "error_type": error_type,
            "meta": meta,
        }

        self.history.append(result)

        failure_summary = []

        # ===== 原有 =====
        if eval_result.get("runtime_error"):
            failure_summary.append("runtime_error")

        # 🔥 只有在没有 judge 时才标记
        if eval_result.get("source") == "reliability_evaluator" and eval_result.get("no_gt"):
            failure_summary.append("no_ground_truth")

        if error_type == "semantic_error":
            failure_summary.append("semantic_error")

        # =================================
        # 🔥 白盒分析（新增）
        # =================================

        if steps:
            last_step = steps[-1]

            observation = last_step.get("observation", "")
            tool = last_step.get("tool", "")
            action = last_step.get("action", "")

            # ===== observation 相关 =====
            if not observation:
                failure_summary.append("empty_observation")

            # ===== tool 使用 =====
            if tool != "code_executor":
                failure_summary.append("wrong_tool_usage")

            # ===== action 检查 =====
            if action != "execute_code":
                failure_summary.append("unexpected_action")

            # ===== 多步异常 =====
            if len(steps) > 3:
                failure_summary.append("too_many_steps")

            # ===== 连续错误 =====
            error_steps = [s for s in steps if s.get("status") == "error"]
            if len(error_steps) >= 2:
                failure_summary.append("repeated_errors")

        # =================================
        # 🔥 pattern mining（保留）
        # =================================
        if len(self.history) >= 3:
            patterns = mine_error_patterns(self.history)
            for p in patterns:
                failure_summary.append(
                    f"{p['error_type']}@{p['doc_type']}:{p['count']}"
                )

        # =================================
        # 🔥 boundary（保留）
        # =================================
        boundary = self.boundary_analyzer.analyze(self.history)

        return {
            "failure_summary": list(set(failure_summary)),  # 🔥 去重
            "num_failures": len(set(failure_summary)),
            "boundary": boundary,
        }

    # =================================
    # 🔥 error type（改成支持 score）
    # =================================
    def _get_error_type(self, eval_result: Dict[str, Any]) -> str:
        if eval_result.get("runtime_error"):
            return "runtime_error"

        if eval_result.get("no_gt"):
            return "unknown"

        # 🔥 统一用 score（兼容 LLM judge）
        score = eval_result.get("score")

        if score is None:
            return "unknown"

        if score > 0:
            return "semantic_error"

        return "normal"