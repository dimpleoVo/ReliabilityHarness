from collections import defaultdict


def run_slice_analysis(results, slice_keys):
    """
    按数据属性做切片分析
    """

    output = {}

    for key in slice_keys:

        bucket = defaultdict(list)

        for r in results:

            value = r["meta"].get(key, "UNKNOWN")

            bucket[value].append(r["metric"])

        slice_result = {}

        for k, v in bucket.items():

            slice_result[k] = sum(v) / len(v)

        output[key] = slice_result

    return output