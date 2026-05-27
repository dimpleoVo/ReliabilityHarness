def mine_badcases(results, top_k=5):

    # 按 metric 从大到小排序（越大越差）
    sorted_results = sorted(
        results,
        key=lambda x: x["metric"],
        reverse=True
    )

    return sorted_results[:top_k]