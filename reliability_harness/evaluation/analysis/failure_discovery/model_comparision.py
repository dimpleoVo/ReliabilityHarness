def compare_model_failures(model_results, slice_key):

    comparison = {}

    for model_name, results in model_results.items():

        bucket = {}

        for r in results:

            value = r["meta"].get(slice_key, "UNKNOWN")

            bucket.setdefault(value, []).append(r["metric"])

        model_scores = {}

        for k, scores in bucket.items():
            model_scores[k] = sum(scores) / len(scores)

        comparison[model_name] = model_scores

    return comparison