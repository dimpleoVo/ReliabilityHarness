import os
import subprocess
import shlex


def run_docker_model(model_config, gt_dir, output_pred_dir):
    """
    使用 docker 运行模型，生成 prediction。
    """

    image = model_config["docker_image"]
    command = model_config["command"]

    gt_dir = os.path.expanduser(gt_dir)
    output_pred_dir = os.path.expanduser(output_pred_dir)

    os.makedirs(output_pred_dir, exist_ok=True)

    docker_cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{gt_dir}:/workspace/gt",
        "-v",
        f"{output_pred_dir}:/workspace/pred",
        image,
    ] + shlex.split(command)

    print("Running docker:", " ".join(docker_cmd))

    subprocess.run(docker_cmd, check=True)