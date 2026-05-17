"""
Tests for metric direction in compute_retry_effectiveness.
No LLM, no Docker, no network.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.loop.retry_effectiveness import (
    compute_retry_effectiveness,
    get_metric_direction,
    METRIC_DIRECTION,
)

TRAJ_TWO = [
    {"step": 1, "traj": {}, "eval": {}},
    {"step": 2, "traj": {}, "eval": {}},
]


def test_edit_distance_improved():
    result = compute_retry_effectiveness(
        trajectory_all=TRAJ_TWO,
        reliability_report={"score_before": 0.8, "score_after": 0.2},
        metric_name="edit_distance",
    )
    assert result["improved"] is True, f"edit_distance 0.8->0.2: expected improved=True, got {result}"
    assert result["metric_direction"] == "lower_is_better"


def test_edit_distance_not_improved():
    result = compute_retry_effectiveness(
        trajectory_all=TRAJ_TWO,
        reliability_report={"score_before": 0.2, "score_after": 0.8},
        metric_name="edit_distance",
    )
    assert result["improved"] is False, f"edit_distance 0.2->0.8: expected improved=False, got {result}"


def test_accuracy_improved():
    result = compute_retry_effectiveness(
        trajectory_all=TRAJ_TWO,
        reliability_report={"score_before": 0.3, "score_after": 0.8},
        metric_name="accuracy",
    )
    assert result["improved"] is True, f"accuracy 0.3->0.8: expected improved=True, got {result}"
    assert result["metric_direction"] == "higher_is_better"


def test_accuracy_not_improved():
    result = compute_retry_effectiveness(
        trajectory_all=TRAJ_TWO,
        reliability_report={"score_before": 0.8, "score_after": 0.3},
        metric_name="accuracy",
    )
    assert result["improved"] is False, f"accuracy 0.8->0.3: expected improved=False, got {result}"


def test_equal_score_not_improved():
    for metric_name in ["edit_distance", "accuracy", "exact_match"]:
        result = compute_retry_effectiveness(
            trajectory_all=TRAJ_TWO,
            reliability_report={"score_before": 0.5, "score_after": 0.5},
            metric_name=metric_name,
        )
        assert result["improved"] is False, (
            f"{metric_name} 0.5->0.5: expected improved=False, got {result}"
        )


def test_metric_direction_registry():
    assert METRIC_DIRECTION["edit_distance"] == "lower_is_better"
    assert METRIC_DIRECTION["accuracy"] == "higher_is_better"
    assert METRIC_DIRECTION["exact_match"] == "higher_is_better"
    assert METRIC_DIRECTION["runtime_error"] == "lower_is_better"


def test_get_metric_direction():
    assert get_metric_direction("edit_distance") == "lower_is_better"
    assert get_metric_direction("accuracy") == "higher_is_better"
    assert get_metric_direction("exact_match") == "higher_is_better"
    assert get_metric_direction("runtime_error") == "lower_is_better"
    assert get_metric_direction("unknown_metric") == "higher_is_better"


def test_explicit_direction_overrides_metric_name():
    # explicit metric_direction must win over metric_name
    result = compute_retry_effectiveness(
        trajectory_all=TRAJ_TWO,
        reliability_report={"score_before": 0.8, "score_after": 0.2},
        metric_name="accuracy",        # higher_is_better → would say not improved
        metric_direction="lower_is_better",  # explicit override → improved
    )
    assert result["improved"] is True, f"explicit override failed: {result}"
    assert result["metric_direction"] == "lower_is_better"


def test_backward_compat_existing_metric_direction_param():
    # Old callers that pass metric_direction= directly must still work unchanged
    result = compute_retry_effectiveness(
        trajectory_all=TRAJ_TWO,
        reliability_report={"score_before": 0.0, "score_after": 1.0},
        metric_direction="higher_is_better",
    )
    assert result["improved"] is True
    assert result["score_delta"] == 1.0


if __name__ == "__main__":
    tests = [
        test_edit_distance_improved,
        test_edit_distance_not_improved,
        test_accuracy_improved,
        test_accuracy_not_improved,
        test_equal_score_not_improved,
        test_metric_direction_registry,
        test_get_metric_direction,
        test_explicit_direction_overrides_metric_name,
        test_backward_compat_existing_metric_direction_param,
    ]

    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL  {test.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    if failed:
        sys.exit(1)
