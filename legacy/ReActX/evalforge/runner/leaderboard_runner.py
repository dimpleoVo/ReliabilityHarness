import copy

from evalforge.runner.eval_runner import run_eval
from evalforge.utils import ensure_dir, dump_json
from evalforge.reports.leaderboard_report import generate_leaderboard_html


def _get_run_name(config: dict) -> str:
    return config.get("project", {}).get("run_name", config.get("run_name", "unnamed_leaderboard"))


def _get_output_dir(config: dict) -> str:
    return config.get("project", {}).get("output_dir", config.get("output_dir", "outputs"))


def _get_benchmark_name(config: dict) -> str:
    return config.get("task", {}).get("benchmark", config.get("benchmark", "unknown"))


def run_leaderboard(config):

    runs = config["leaderboard"]["runs"]
    slice_keys = config.get("analysis", {}).get("slice_keys", [])

    summaries = []

    for run in runs:

        eval_config = copy.deepcopy(config)
        eval_config["mode"] = "eval"

        eval_config["project"]["run_name"] = run["name"]
        eval_config["dataset"]["pred_dir"] = f"{run['base_dir']}/pred"

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

    leaderboard_json = {
        "benchmark": benchmark_name,
        "run_name": run_name,
        "num_models": len(summaries),
        "results": summaries,
    }

    dump_json(leaderboard_json, str(output_dir / "leaderboard.json"))

    generate_leaderboard_html(
        str(output_dir / "leaderboard.html"),
        summaries,
        slice_keys,
    )

    return leaderboard_json