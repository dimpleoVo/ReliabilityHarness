import argparse

from evalforge.utils import load_yaml
from evalforge.runner.eval_runner import run_eval
from evalforge.runner.leaderboard_runner import run_leaderboard
from evalforge.runner.benchmark_runner import run_benchmark


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = load_yaml(args.config)
    mode = config.get("mode", "eval").strip().lower()

    if mode == "leaderboard":
        result = run_leaderboard(config)

        print("\n=== EvalForge Leaderboard Summary ===")
        print("benchmark:", result["benchmark"])
        print("run_name:", result["run_name"])
        print("num_models:", result["num_models"])
        for item in result["results"]:
            print(
                item["model_name"],
                "edit_distance=",
                item["overall_edit_distance"],
                "llm_judge=",
                item["overall_llm_judge_score"],
                "invalid_outputs=",
                item["num_invalid_outputs"],
            )

    elif mode == "benchmark":
        result = run_benchmark(config)

        print("\n=== EvalForge Benchmark Summary ===")
        print("benchmark:", result["benchmark"])
        print("run_name:", result["run_name"])
        print("num_models:", result["num_models"])
        for item in result["results"]:
            print(
                item["model_name"],
                "edit_distance=",
                item["overall_edit_distance"],
                "llm_judge=",
                item["overall_llm_judge_score"],
                "invalid_outputs=",
                item["num_invalid_outputs"],
            )

    else:
        result = run_eval(config)

        print("\n=== EvalForge Summary ===")
        print("benchmark:", result["benchmark"])
        print("run_name:", result["run_name"])
        print("aggregate_metrics:", result["aggregate_metrics"])
        print("num_samples:", result["num_samples"])
        print("num_invalid_outputs:", result["num_invalid_outputs"])
        print("num_badcases:", result["num_badcases"])


if __name__ == "__main__":
    main()