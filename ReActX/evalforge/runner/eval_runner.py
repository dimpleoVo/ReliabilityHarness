import evalforge.tasks.recognition_task
import evalforge.tasks.qa_task
import evalforge.tasks.detection_task
from collections import Counter

from evalforge.datasets.registry import get_dataset
from evalforge.metrics.edit_distance import normalized_edit_distance
from evalforge.metrics.llm_judge import get_llm_judge_score

from evalforge.analysis.invalid_output import detect_invalid_output
from evalforge.analysis.error_attribution import attribute_error
from evalforge.analysis.slice import run_slice_analysis
from evalforge.analysis.badcase import mine_badcases
from evalforge.analysis.error_patterns import mine_error_patterns

from evalforge.reports.report import generate_report, generate_badcase_html
from evalforge.reports.badcase_debugger import write_badcase_debugger_html
from evalforge.utils import ensure_dir, dump_json
from evalforge.tasks.task_registry import get_task

from evalforge.analysis.failure_discovery.weak_slice import detect_weak_slices
from evalforge.analysis.failure_discovery.failure_boundary import detect_failure_boundaries
from evalforge.analysis.failure_discovery.risk_region import discover_risk_regions
from evalforge.datasets.registry import get_dataset
from evalforge.tasks.task_registry import get_task, auto_import_tasks

auto_import_tasks()

def _get_run_name(config: dict) -> str:
    return config.get("project", {}).get("run_name", config.get("run_name", "unnamed_run"))


def _get_output_dir(config: dict) -> str:
    return config.get("project", {}).get("output_dir", config.get("output_dir", "outputs"))


def _get_benchmark_name(config: dict) -> str:
    return config.get("task", {}).get("benchmark", config.get("benchmark", "unknown"))


def run_eval(config: dict):
    samples = get_dataset(config)
    results = []
    invalid_outputs = []

    judge_cfg = config.get("judge", config.get("judge_model", {"mock": True}))
    analysis_cfg = config.get("analysis", {})

    slice_keys = analysis_cfg.get("slice_keys", [])
    top_k_badcases = int(analysis_cfg.get("top_k_badcases", analysis_cfg.get("top_k", 5)))



    for sample in samples:
        gt = sample.get("gt", "")
        pred = sample.get("pred", "")
        meta = sample.get("meta", {})

        task_name = sample.get("task", "recognition")

        task = get_task(task_name)

        # ---------- Task-aware evaluation ----------
        primary_score = task.evaluate_primary(sample)
        secondary_results = task.evaluate_secondary(sample)
        risk_inputs = task.map_to_risk_inputs(
             primary_score,
             secondary_results
             )
        failure_signals = task.detect_failure_signals(
             sample,
             primary_score
             )
        ed_score = primary_score
        # -------------------------------------------

        llm_score = get_llm_judge_score(gt, pred, judge_cfg)

        invalid_error_type = detect_invalid_output(pred)
        if invalid_error_type is not None:
            invalid_outputs.append({
                "id": sample["id"],
                "type": invalid_error_type
            })

        error_type = attribute_error(
            pred_text=pred,
            metric=ed_score,
            invalid_error_type=invalid_error_type,
        )

        results.append({
            "id": sample["id"],
            "metric": ed_score,
            "score": ed_score,   # 兼容 badcase_debugger 里的 score 字段
            "llm_score": llm_score,
            "secondary": secondary_results,
            "risk_inputs": risk_inputs,
            "failure_signals": failure_signals,
            "gt": gt,
            "pred": pred,
            "meta": meta,
            "error_type": error_type,
        })

    avg_ed = sum(r["metric"] for r in results) / len(results) if results else 0.0
    avg_llm = sum(r["llm_score"] for r in results) / len(results) if results else 0.0

    slice_result = run_slice_analysis(results, slice_keys) if slice_keys else {}
    badcases = mine_badcases(results, top_k=top_k_badcases)
    error_patterns = mine_error_patterns(results, top_k=top_k_badcases)
    error_counter = Counter(r["error_type"] for r in results)

    weak_slices = detect_weak_slices(results, slice_keys)
    failure_boundaries = detect_failure_boundaries(results, slice_keys)

    risk_regions = discover_risk_regions(
    results=results,
    slice_keys=slice_keys,
    top_k=int(analysis_cfg.get("top_k_risk_regions", 10)),
    min_samples=int(analysis_cfg.get("min_risk_region_samples", 3)),
)

    run_name = _get_run_name(config)
    output_root = _get_output_dir(config)
    benchmark_name = _get_benchmark_name(config)

    output_dir = ensure_dir(f"{output_root}/{run_name}")

    report_data = {
        "benchmark": benchmark_name,
        "run_name": run_name,
        "aggregate_metrics": {
            "edit_distance": avg_ed,
            "llm_judge_score": avg_llm,
        },
        "num_samples": len(results),
        "num_invalid_outputs": len(invalid_outputs),
        "num_badcases": len(badcases),
        "slice_analysis": slice_result,
        "weak_slices": weak_slices,
        "failure_boundaries": failure_boundaries,
        "risk_regions": risk_regions,
        "error_distribution": dict(error_counter),
        "error_patterns": error_patterns,
        "invalid_outputs": invalid_outputs,
        "results": results,
        "badcases": badcases,
    }

    generate_report(str(output_dir / "report.json"), report_data)
    dump_json(slice_result, str(output_dir / "slice_report.json"))
    dump_json(dict(error_counter), str(output_dir / "error_report.json"))
    dump_json(risk_regions, str(output_dir / "risk_regions.json"))
    generate_badcase_html(str(output_dir / "badcases.html"), badcases)
    write_badcase_debugger_html(
        out_path=str(output_dir / "badcase_debugger.html"),
        badcases=badcases,
    )

    return {
        "benchmark": benchmark_name,
        "run_name": run_name,
        "aggregate_metrics": {
            "edit_distance": avg_ed,
            "llm_judge_score": avg_llm,
        },
        "num_samples": len(results),
        "num_invalid_outputs": len(invalid_outputs),
        "num_badcases": len(badcases),
        "slice_analysis": slice_result,
        "error_distribution": dict(error_counter),
        "error_patterns": error_patterns,
        "results": results,
        "badcases": badcases,
    }