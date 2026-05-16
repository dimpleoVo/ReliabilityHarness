import os


def load_omnidocbench(gt_dir, pred_dir):

    gt_dir = os.path.expanduser(gt_dir)
    pred_dir = os.path.expanduser(pred_dir)

    samples = []

    for fname in os.listdir(gt_dir):

        if not fname.endswith(".md"):
            continue

        gt_path = os.path.join(gt_dir, fname)
        pred_path = os.path.join(pred_dir, fname)

        with open(gt_path, "r", encoding="utf-8") as f:
            gt_text = f.read()

        if os.path.exists(pred_path):
            with open(pred_path, "r", encoding="utf-8") as f:
                pred_text = f.read()
        else:
            pred_text = ""

        samples.append(
            {
                "id": fname,
                "task": "recognition",
                "gt": gt_text,
                "pred": pred_text,
                "meta": {
                    "doc_type": fname.split("_")[0]
                },
            }
        )

    return samples