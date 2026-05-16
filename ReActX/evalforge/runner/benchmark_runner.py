import copy

from evalforge.runner.eval_runner import run_eval
from evalforge.scheduler.parallel_scheduler import run_predictions_parallel
from evalforge.utils import ensure_dir, dump_json
from evalforge.reports.leaderboard_report import generate_leaderboard_html


def _get_run_name(config: dict) -> str:
    return config.get("project", {}).get("run_name", config.get("run_name", "unnamed_benchmark"))


def _get_output_dir(config: dict) -> str:
    return config.get("project", {}).get("output_dir", config.get("output_dir", "outputs"))


def _get_benchmark_name(config: dict) -> str:
    return config.get("task", {}).get("benchmark", config.get("benchmark", "unknown"))


def run_benchmark(config):
    scheduler_cfg = config.get("scheduler", {})
    max_workers = int(scheduler_cfg.get("max_workers", 2))
    slice_keys = config.get("analysis", {}).get("slice_keys", [])

    prepared_runs = run_predictions_parallel(config, max_workers=max_workers)

    summaries = []

    for run in prepared_runs:
        eval_config = copy.deepcopy(config)
        eval_config["mode"] = "eval"
        eval_config["project"]["run_name"] = run["name"]
        eval_config["dataset"]["pred_dir"] = run["pred_dir"]

        result = run_eval(eval_config)

        summaries.append({
            "model_name": run["name"],
            "num_samples": result["num_samples"],
            "overall_edit_distance": result["aggregate_metrics"]["edit_distance"],
            "overall_llm_judge_score": result["aggregate_metrics"]["llm_judge_score"],
            "num_invalid_outputs": result["num_invalid_outputs"],
            "num_badcases": result["num_badcases"],
            "slice_analysis": result.get("slice_analysis", {}),
            "error_distribution": result.get("error_distribution", {}),
        })

    summaries.sort(key=lambda x: x["overall_edit_distance"])

    run_name = _get_run_name(config)
    output_root = _get_output_dir(config)
    benchmark_name = _get_benchmark_name(config)

    output_dir = ensure_dir(f"{output_root}/{run_name}")

    benchmark_json = {
        "benchmark": benchmark_name,
        "run_name": run_name,
        "num_models": len(summaries),
        "results": summaries,
    }

    dump_json(benchmark_json, str(output_dir / "leaderboard.json"))
    generate_leaderboard_html(
        str(output_dir / "leaderboard.html"),
        summaries,
        slice_keys,
    )

    return benchmark_json