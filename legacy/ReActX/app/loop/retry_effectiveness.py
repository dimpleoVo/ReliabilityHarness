# Per-metric direction: determines whether higher or lower scores indicate improvement.
METRIC_DIRECTION = {
    "edit_distance": "lower_is_better",
    "error_count": "lower_is_better",
    "runtime_error_rate": "lower_is_better",
    "runtime_error": "lower_is_better",
    "accuracy": "higher_is_better",
    "exact_match": "higher_is_better",
}


def get_metric_direction(metric_name: str) -> str:
    """Return direction for a named metric; defaults to 'higher_is_better' for unknowns."""
    return METRIC_DIRECTION.get(metric_name, "higher_is_better")


def compute_retry_effectiveness(
    trajectory_all: list,
    eval_results: list | None = None,
    reliability_report: dict | None = None,
    metric_direction: str | None = None,
    metric_name: str | None = None,
) -> dict:
    """
    metric_direction takes precedence if supplied explicitly.
    Otherwise direction is resolved from metric_name via METRIC_DIRECTION.
    Unknown metric_name defaults to 'higher_is_better'.
    """
    report = reliability_report or {}
    attempts = len(trajectory_all)
    retry_triggered = attempts > 1

    # Resolve direction: explicit override > per-metric lookup > global default
    if metric_direction is not None:
        direction = metric_direction
    elif metric_name is not None:
        direction = get_metric_direction(metric_name)
    else:
        direction = "higher_is_better"

    score_before = report.get("score_before")
    score_after = report.get("score_after")

    if score_before is not None and score_after is not None:
        if direction == "lower_is_better":
            score_delta = score_before - score_after
            improved = score_after < score_before
            recovered_from_failure = (
                retry_triggered
                and score_before > 0.0
                and score_after <= 0.0
            )
        else:  # higher_is_better
            score_delta = score_after - score_before
            improved = score_after > score_before
            recovered_from_failure = (
                retry_triggered
                and score_before < 1.0
                and score_after >= 1.0
            )
    else:
        score_delta = None
        improved = False
        recovered_from_failure = False

    return {
        "retry_triggered": retry_triggered,
        "attempts": attempts,
        "score_before": score_before,
        "score_after": score_after,
        "score_delta": score_delta,
        "improved": improved,
        "recovered_from_failure": recovered_from_failure,
        "metric_direction": direction,
    }
