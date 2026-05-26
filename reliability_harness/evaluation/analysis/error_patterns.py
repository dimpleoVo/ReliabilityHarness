from collections import Counter


def mine_error_patterns(results, top_k=5):
    """
    从结果中挖掘常见错误模式
    """

    patterns = []

    for r in results:
        error_type = r.get("error_type", "normal")
        doc_type = r.get("meta", {}).get("doc_type", "unknown")

        if error_type == "normal":
            continue

        patterns.append((error_type, doc_type))

    counter = Counter(patterns)

    top_patterns = []

    for (err, doc), cnt in counter.most_common(top_k):
        top_patterns.append({
            "error_type": err,
            "doc_type": doc,
            "count": cnt
        })

    return top_patterns