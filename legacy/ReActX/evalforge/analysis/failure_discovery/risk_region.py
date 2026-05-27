from collections import defaultdict
from itertools import combinations
import math


def _safe_mean(values):
    if not values:
        return 0.0
    return sum(values) / len(values)


def _safe_std(values):
    if not values:
        return 0.0
    mean_v = _safe_mean(values)
    var = sum((x - mean_v) ** 2 for x in values) / len(values)
    return math.sqrt(var)


def _clip01(x):
    return max(0.0, min(1.0, x))


def _aggregate_region_stats(region_name, region_meta, samples):
    """
    对某个 region 内的样本聚合统计
    samples: list[dict], 每个元素是 results 里的单条结果
    """
    perf_drops = []
    invalid_rates = []
    severe_rates = []

    for s in samples:
        risk = s.get("risk_inputs", {}) or {}
        perf_drops.append(float(risk.get("performance_drop", s.get("metric", 0.0))))
        invalid_rates.append(float(risk.get("invalid_rate", 0.0)))
        severe_rates.append(float(risk.get("severe_error_rate", 0.0)))

    avg_perf = _safe_mean(perf_drops)
    avg_invalid = _safe_mean(invalid_rates)
    avg_severe = _safe_mean(severe_rates)
    instability = _clip01(_safe_std(perf_drops))

    # v1 启发式风险分数
    risk_score = (
        0.40 * avg_perf +
        0.25 * avg_invalid +
        0.25 * avg_severe +
        0.10 * instability
    )

    return {
        "region_name": region_name,
        "region_meta": region_meta,
        "sample_count": len(samples),
        "avg_performance_drop": round(avg_perf, 6),
        "invalid_rate": round(avg_invalid, 6),
        "severe_error_rate": round(avg_severe, 6),
        "instability": round(instability, 6),
        "risk_score": round(risk_score, 6),
    }


def discover_single_risk_regions(results, slice_keys, top_k=10, min_samples=3):
    """
    发现单维高风险区域
    例：
      doc_type=table
      language=zh
    """
    regions = []

    for key in slice_keys:
        bucket = defaultdict(list)

        for r in results:
            value = r.get("meta", {}).get(key, "UNKNOWN")
            bucket[value].append(r)

        for value, samples in bucket.items():
            if len(samples) < min_samples:
                continue

            region_name = f"{key}={value}"
            region_meta = {key: value}

            stats = _aggregate_region_stats(region_name, region_meta, samples)
            regions.append(stats)

    regions.sort(key=lambda x: x["risk_score"], reverse=True)
    return regions[:top_k]


def discover_pair_risk_regions(results, slice_keys, top_k=10, min_samples=3):
    """
    发现二维高风险边界
    例：
      doc_type=table & language=zh
    """
    regions = []

    for key1, key2 in combinations(slice_keys, 2):
        bucket = defaultdict(list)

        for r in results:
            meta = r.get("meta", {}) or {}
            value1 = meta.get(key1, "UNKNOWN")
            value2 = meta.get(key2, "UNKNOWN")
            bucket[(value1, value2)].append(r)

        for (value1, value2), samples in bucket.items():
            if len(samples) < min_samples:
                continue

            region_name = f"{key1}={value1} & {key2}={value2}"
            region_meta = {
                key1: value1,
                key2: value2,
            }

            stats = _aggregate_region_stats(region_name, region_meta, samples)
            regions.append(stats)

    regions.sort(key=lambda x: x["risk_score"], reverse=True)
    return regions[:top_k]


def discover_risk_regions(results, slice_keys, top_k=10, min_samples=3):
    """
    总入口
    """
    if not results or not slice_keys:
        return {
            "single_regions": [],
            "pair_regions": [],
        }

    single_regions = discover_single_risk_regions(
        results=results,
        slice_keys=slice_keys,
        top_k=top_k,
        min_samples=min_samples,
    )

    pair_regions = discover_pair_risk_regions(
        results=results,
        slice_keys=slice_keys,
        top_k=top_k,
        min_samples=min_samples,
    )

    return {
        "single_regions": single_regions,
        "pair_regions": pair_regions,
    }