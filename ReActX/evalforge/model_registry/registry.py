import os
import shutil
from evalforge.model_registry.docker_runner import run_docker_model
from evalforge.model_registry.openai_compat_runner import run_openai_compat_model

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def model_run_copy(model_config, gt_dir, output_pred_dir):
    """
    v5 的第一版先用“复制已有 prediction”模拟模型推理。
    这样可以先打通平台架构。
    后面再替换成真实 docker/model inference。
    """
    ensure_dir(output_pred_dir)

    source_pred_dir = os.path.expanduser(model_config["source_pred_dir"])

    for fname in os.listdir(source_pred_dir):
        src = os.path.join(source_pred_dir, fname)
        dst = os.path.join(output_pred_dir, fname)

        if os.path.isfile(src):
            shutil.copy2(src, dst)


MODEL_REGISTRY = {
    "copy_runner": model_run_copy,
    "docker_runner": run_docker_model,
    "openai_compat_runner": run_openai_compat_model,
}


def get_model_runner(model_type):
    if model_type not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model runner: {model_type}")
    return MODEL_REGISTRY[model_type]