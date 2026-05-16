from collections import defaultdict


def detect_weak_slices(results, slice_keys, top_k=3):
    """
    自动发现表现最差的 slice
    """

    slice_scores = {}

    for key in slice_keys:
        bucket = defaultdict(list)

        for r in results:
            value = r["meta"].get(key, "UNKNOWN")
            bucket[value].append(r["metric"])

        avg_scores = []

        for v, scores in bucket.items():
            avg = sum(scores) / len(scores)
            avg_scores.append({
                "slice_key": key,
                "slice_value": v,
                "score": avg
            })

        avg_scores.sort(key=lambda x: x["score"], reverse=True)

        slice_scores[key] = avg_scores[:top_k]

    return slice_scores