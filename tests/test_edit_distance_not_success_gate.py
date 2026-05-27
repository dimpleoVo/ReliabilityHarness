"""
Focused tests: edit_distance must not act as success gate.

Verifies:
1. evaluator.py no longer sets primary_metric_name="edit_distance"
2. edit_distance alone does not make _derive_final_success return True
3. edit_distance alone does not make is_eval_success return True
4. explicit final_success / task_success / test_passed / tests_passed succeed
5. recovery_success requires failed first attempt + explicit success later
"""
import pytest

from reliability_harness.evaluation.runtime_eval.evaluator import Evaluator
from reliability_harness.artifacts.run_artifact import _derive_final_success
from reliability_harness.runtime.loop.success_gate import is_eval_success


# ---------------------------------------------------------------------------
# A. evaluator.py — primary_metric_name must not be "edit_distance"
# ---------------------------------------------------------------------------
class TestEvaluatorPrimaryMetric:
    def _eval(self, pred, gt):
        return Evaluator(metrics=["edit_distance"]).evaluate(
            {"prediction": pred, "ground_truth": gt, "meta": {}}
        )

    def test_primary_metric_name_is_not_edit_distance(self):
        result = self._eval("hello", "world")
        assert result["primary_metric_name"] != "edit_distance"

    def test_score_is_none(self):
        result = self._eval("hello", "hello")
        assert result["score"] is None

    def test_final_success_is_none(self):
        result = self._eval("x", "x")
        assert result["final_success"] is None

    def test_edit_distance_preserved_in_auxiliary_metrics(self):
        result = self._eval("hello", "hello")
        assert "edit_distance" in result["metrics"]
        assert "edit_distance" in result["auxiliary_metrics"]

    def test_no_gt_still_correct(self):
        result = Evaluator(metrics=["edit_distance"]).evaluate(
            {"prediction": "x", "ground_truth": None, "meta": {}}
        )
        assert result["primary_metric_name"] is None
        assert result["score"] is None
        assert result["no_gt"] is True


# ---------------------------------------------------------------------------
# B. run_artifact._derive_final_success — no edit_distance threshold
# ---------------------------------------------------------------------------
class TestDeriveFinalSuccess:
    def _entry(self, step_success=None):
        return {"step_success": step_success}

    def test_edit_distance_low_does_not_succeed(self):
        entry = self._entry()
        eval_result = {"metrics": {"edit_distance": 0.01}}
        result = _derive_final_success(entry, False, 0.01, eval_result)
        assert result is None or result is False

    def test_edit_distance_zero_does_not_succeed(self):
        entry = self._entry()
        eval_result = {"metrics": {"edit_distance": 0.0}}
        result = _derive_final_success(entry, False, 0.0, eval_result)
        assert result is None or result is False

    def test_explicit_final_success_true(self):
        entry = self._entry()
        assert _derive_final_success(entry, False, None, {"final_success": True}) is True

    def test_explicit_final_success_false(self):
        entry = self._entry()
        assert _derive_final_success(entry, False, None, {"final_success": False}) is False

    def test_explicit_task_success_true(self):
        entry = self._entry()
        assert _derive_final_success(entry, False, None, {"task_success": True}) is True

    def test_explicit_test_passed_true(self):
        entry = self._entry()
        assert _derive_final_success(entry, False, None, {"test_passed": True}) is True

    def test_explicit_tests_passed_true(self):
        entry = self._entry()
        assert _derive_final_success(entry, False, None, {"tests_passed": True}) is True

    def test_runtime_error_overrides_final_success(self):
        entry = self._entry()
        assert _derive_final_success(entry, True, None, {"final_success": True}) is False

    def test_step_success_explicit_takes_priority(self):
        entry = self._entry(step_success=True)
        eval_result = {"metrics": {"edit_distance": 0.99}}
        assert _derive_final_success(entry, False, 0.99, eval_result) is True

    def test_step_success_false_takes_priority(self):
        entry = self._entry(step_success=False)
        eval_result = {"final_success": True}
        assert _derive_final_success(entry, False, None, eval_result) is False

    def test_no_signal_returns_none_or_false(self):
        entry = self._entry()
        result = _derive_final_success(entry, False, None, {})
        assert result is None or result is False


# ---------------------------------------------------------------------------
# C. closed_loop_runner.is_eval_success — no edit_distance threshold
# ---------------------------------------------------------------------------
class TestIsEvalSuccess:
    def test_edit_distance_low_does_not_succeed(self):
        assert is_eval_success({"metrics": {"edit_distance": 0.01}}) is False

    def test_edit_distance_zero_does_not_succeed(self):
        assert is_eval_success({"metrics": {"edit_distance": 0.0}}) is False

    def test_edit_distance_below_old_threshold_does_not_succeed(self):
        assert is_eval_success({"metrics": {"edit_distance": 0.04}}) is False

    def test_explicit_final_success_true(self):
        assert is_eval_success({"final_success": True}) is True

    def test_explicit_final_success_false(self):
        assert is_eval_success({"final_success": False}) is False

    def test_explicit_task_success_true(self):
        assert is_eval_success({"task_success": True}) is True

    def test_explicit_test_passed_true(self):
        assert is_eval_success({"test_passed": True}) is True

    def test_explicit_tests_passed_true(self):
        assert is_eval_success({"tests_passed": True}) is True

    def test_runtime_error_always_fails(self):
        assert is_eval_success({"final_success": True, "runtime_error": True}) is False

    def test_no_signal_returns_false(self):
        assert is_eval_success({}) is False

    def test_llm_judge_correct_true(self):
        assert is_eval_success({"judge": {"correct": True}}) is True

    def test_llm_judge_correct_false(self):
        assert is_eval_success({"judge": {"correct": False}}) is False

    def test_llm_judge_metric_high(self):
        assert is_eval_success({"metrics": {"llm_judge": 0.9}}) is True

    def test_llm_judge_metric_low(self):
        assert is_eval_success({"metrics": {"llm_judge": 0.5}}) is False


# ---------------------------------------------------------------------------
# D. recovery_success — depends on explicit failure then explicit success
# ---------------------------------------------------------------------------
class TestRecoverySuccessNotFromEditDistance:
    def test_recovery_requires_explicit_first_fail_then_success(self):
        first_eval = {"metrics": {"edit_distance": 0.01}}  # no longer success
        final_eval = {"final_success": True}

        initially_failed = not is_eval_success(first_eval)
        retry_triggered = True
        success = is_eval_success(final_eval)
        recovery_success = bool(initially_failed and retry_triggered and success)

        assert initially_failed is True
        assert success is True
        assert recovery_success is True

    def test_no_recovery_when_first_attempt_was_explicit_success(self):
        first_eval = {"final_success": True}
        final_eval = {"final_success": True}

        initially_failed = not is_eval_success(first_eval)
        recovery_success = bool(initially_failed and True and True)

        assert initially_failed is False
        assert recovery_success is False

    def test_no_recovery_when_final_attempt_not_explicit_success(self):
        first_eval = {}
        final_eval = {"metrics": {"edit_distance": 0.0}}

        initially_failed = not is_eval_success(first_eval)
        success = is_eval_success(final_eval)
        recovery_success = bool(initially_failed and True and success)

        assert success is False
        assert recovery_success is False
