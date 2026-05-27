"""
Test: dataset_loader resolves path via REACTX_DATASET_PATH env var.
No real dataset file needed.
"""
import json
import os
import tempfile

# Create a fake dataset in a temp file
FAKE_DATASET = [
    {"task": "print hello world", "gt": "hello world"},
    {"task": "add 1 and 2", "gt": "3"},
]

with tempfile.NamedTemporaryFile(
    mode="w", suffix=".json", delete=False, encoding="utf-8"
) as f:
    json.dump(FAKE_DATASET, f)
    fake_path = f.name

os.environ["REACTX_DATASET_PATH"] = fake_path

# Re-import after env var is set (loader reads env at call time via _resolve_dataset_path)
import importlib
import utils.dataset_loader as _loader
importlib.reload(_loader)

data = _loader.load_dataset()

assert isinstance(data, list), "load_dataset() should return a list"
assert len(data) == 2, f"expected 2 items, got {len(data)}"
assert data[0]["task"] == "print hello world"
assert data[0]["gt"] == "hello world"

# Also verify get_ground_truth works via env path
gt = _loader.get_ground_truth("print hello world")
assert gt == "hello world", f"expected 'hello world', got {gt}"

# Cleanup
os.unlink(fake_path)

print("[TEST PASS] dataset loader path resolved correctly")
