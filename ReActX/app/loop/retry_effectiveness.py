def compute_retry_effectiveness(
    trajectory_all: list,
    eval_results: list | None = None,
    reliability_report: dict | None = None,
    metric_direction: str = "higher_is_better",
) -> dict:
    report = reliability_report or {}
    attempts = len(trajectory_all)
    retry_triggered = attempts > 1

    score_before = report.get("score_before")
    score_after = report.get("score_after")

    if score_before is not None and score_after is not None:
        if metric_direction == "lower_is_better":
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
    }
