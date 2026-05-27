"""
Schema validation for ReActX/data/reliability_tasks.json.
No LLM, no Docker, no external deps. Pure JSON structure checks.
Run: cd ReActX && python test_reliability_tasks_schema.py
"""
import sys
import os
import json

TASKS_PATH = os.path.join(os.path.dirname(__file__), "data", "reliability_tasks.json")

VALID_CATEGORIES  = {"runtime_error", "timeout", "semantic_error", "recoverable_retry", "memory_assisted"}
VALID_DIFFICULTIES = {"easy", "medium"}
VALID_METRICS     = {"exact_match", "edit_distance"}
VALID_DIRECTIONS  = {"higher_is_better", "lower_is_better"}
REQUIRED_FIELDS   = {"id", "category", "task", "expected_output", "failure_mode", "difficulty", "why_relevant", "evaluation"}
BANNED_KEYWORDS   = ["input(", "requests", "open(", "pandas", "numpy", "random", "datetime"]

EXPECTED_TOTAL    = 20
EXPECTED_PER_CAT  = 4


def _load() -> list:
    with open(TASKS_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_dataset_exists():
    assert os.path.exists(TASKS_PATH), f"Dataset not found at: {TASKS_PATH}"


def test_json_loadable():
    data = _load()
    assert isinstance(data, list), f"Root must be a JSON array, got {type(data).__name__}"


def test_task_count():
    data = _load()
    assert len(data) == EXPECTED_TOTAL, f"Expected {EXPECTED_TOTAL} tasks, got {len(data)}"


def test_unique_ids():
    data = _load()
    ids = [t["id"] for t in data]
    seen, dupes = set(), set()
    for i in ids:
        (dupes if i in seen else seen).add(i)
    assert not dupes, f"Duplicate task ids: {sorted(dupes)}"


def test_category_distribution():
    data = _load()
    counts = {cat: 0 for cat in VALID_CATEGORIES}
    for t in data:
        cat = t.get("category")
        assert cat in VALID_CATEGORIES, f"Task {t.get('id', '?')}: invalid category {cat!r}"
        counts[cat] += 1
    for cat, n in counts.items():
        assert n == EXPECTED_PER_CAT, f"Category '{cat}' has {n} tasks, expected {EXPECTED_PER_CAT}"


def test_required_fields():
    data = _load()
    for t in data:
        missing = REQUIRED_FIELDS - set(t.keys())
        assert not missing, f"Task {t.get('id', '?')} missing fields: {sorted(missing)}"
        d = t.get("difficulty")
        assert d in VALID_DIFFICULTIES, (
            f"Task {t['id']}: difficulty={d!r} not in {sorted(VALID_DIFFICULTIES)}"
        )
        for field in ("task", "expected_output", "why_relevant"):
            val = t.get(field, "")
            assert val and str(val).strip(), f"Task {t['id']}: field '{field}' must not be empty"


def test_evaluation_schema():
    data = _load()
    for t in data:
        ev = t.get("evaluation")
        assert isinstance(ev, dict), f"Task {t.get('id', '?')}: 'evaluation' must be a dict"
        metric = ev.get("metric")
        direction = ev.get("direction")
        assert metric in VALID_METRICS, (
            f"Task {t['id']}: evaluation.metric={metric!r} not in {sorted(VALID_METRICS)}"
        )
        assert direction in VALID_DIRECTIONS, (
            f"Task {t['id']}: evaluation.direction={direction!r} not in {sorted(VALID_DIRECTIONS)}"
        )


def test_no_external_dependencies():
    data = _load()
    for t in data:
        task_text = t.get("task", "")
        for kw in BANNED_KEYWORDS:
            assert kw not in task_text, (
                f"Task {t['id']}: task text contains banned keyword {kw!r}"
            )


if __name__ == "__main__":
    tests = [
        test_dataset_exists,
        test_json_loadable,
        test_task_count,
        test_unique_ids,
        test_category_distribution,
        test_required_fields,
        test_evaluation_schema,
        test_no_external_dependencies,
    ]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL  {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR {test.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    if failed:
        sys.exit(1)
