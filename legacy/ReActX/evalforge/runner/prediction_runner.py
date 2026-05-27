import os

from evalforge.model_registry import get_model_runner
from evalforge.utils import dump_json


def run_predictions(config):
    prepared_runs = []

    gt_dir = os.path.expanduser(config["dataset"]["gt_dir"])
    run_root = os.path.expanduser(
        config.get("project", {}).get(
            "prediction_output_root",
            config.get("prediction_output_root", "eval_data/runs")
        )
    )
    os.makedirs(run_root, exist_ok=True)

    for model in config["models"]:
        model_name = model["name"]
        runner_type = model["runner_type"]
        runner = get_model_runner(runner_type)

        base_dir = os.path.join(run_root, model_name)
        pred_dir = os.path.join(base_dir, "pred")
        os.makedirs(pred_dir, exist_ok=True)

        runner(model, gt_dir, pred_dir)

        meta = {
            "model_name": model_name,
            "runner_type": runner_type,
            "benchmark": config.get("task", {}).get("benchmark", config.get("benchmark", "unknown")),
            "gt_dir": gt_dir,
            "pred_dir": pred_dir,
        }
        dump_json(meta, os.path.join(base_dir, "meta.json"))

        prepared_runs.append({
            "name": model_name,
            "base_dir": base_dir,
            "pred_dir": pred_dir,
            "meta_path": os.path.join(base_dir, "meta.json"),
        })

    return prepared_runs