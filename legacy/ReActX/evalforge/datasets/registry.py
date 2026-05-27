from evalforge.datasets.omnidocbench_loader import load_omnidocbench
from evalforge.datasets.docai_demo import load_docai_demo


def get_dataset(config):
    dataset_cfg = config["dataset"]
    name = dataset_cfg["name"]

    if name == "docai_demo":
        return load_docai_demo()

    if name == "omnidocbench":
        gt_dir = dataset_cfg["gt_dir"]
        pred_dir = dataset_cfg["pred_dir"]
        return load_omnidocbench(gt_dir, pred_dir)

    raise ValueError(f"Unknown dataset: {name}")