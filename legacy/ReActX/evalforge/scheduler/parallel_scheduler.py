import concurrent.futures
import copy

from evalforge.runner.prediction_runner import run_predictions


def _run_single_model(global_config, model_config):
    single_config = copy.deepcopy(global_config)
    single_config["models"] = [model_config]

    runs = run_predictions(single_config)
    return runs[0] if runs else None


def run_predictions_parallel(config, max_workers=2):
    models = config["models"]
    prepared_runs = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(_run_single_model, config, model)
            for model in models
        ]

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                prepared_runs.append(result)

    prepared_runs.sort(key=lambda x: x["name"])
    return prepared_runs