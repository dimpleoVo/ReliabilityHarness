from collections import defaultdict


def detect_failure_boundaries(results, slice_keys, threshold=0.8):
    """
    寻找 metric 超过阈值的 slice 组合
    """

    boundaries = []

    for r in results:

        if r["metric"] < threshold:
            continue

        boundary = {}

        for key in slice_keys:
            boundary[key] = r["meta"].get(key, "UNKNOWN")

        boundaries.append(boundary)

    return boundaries