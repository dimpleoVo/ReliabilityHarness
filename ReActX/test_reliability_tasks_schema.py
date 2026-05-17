"""
Schema validation for ReActX/data/reliability_tasks.json.
No LLM, no Docker. Pure JSON structure checks.
Run with: python test_reliability_tasks_schema.py
"""
import sys
import os
import json

TASKS_PATH = os.path.join(os.path.dirname(__file__), "data", "reliability_tasks.json")

REQUIRED_FIELDS   = {"id", "category", "task", "expected_output", "expected_failure_modes", "difficulty"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}


def _load() -> list:
    with open(TASKS_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_json_loadable():
    data = _load()
    assert isinstance(data, list), f"Expected list at root, got {type(data).__name__}"


def test_exactly_20_tasks():
    data = _load()
    assert len(data) == 20, f"Expected 20 tasks, got {len(data)}"


def test_ids_are_unique():
    data = _load()
    ids = [t["id"] for t in data]
    dupes = [i for i in ids if ids.count(i) > 1]
    assert not dupes, f"Duplicate ids: {sorted(set(dupes))}"


def test_required_fields_present():
    data = _load()
    for t in data:
        missing = REQUIRED_FIELDS - set(t.keys())
        assert not missing, f"Task {t.get('id', '?')} missing fields: {sorted(missing)}"


def test_expected_failure_modes_is_list():
    data = _load()
    for t in data:
        modes = t.get("expected_failure_modes")
        assert isinstance(modes, list), (
            f"Task {t['id']}: expected_failure_modes must be list, got {type(modes).__name__}"
        )


def test_difficulty_values_valid():
    data = _load()
    for t in data:
        d = t.get("difficulty")
        assert d in VALID_DIFFICULTIES, (
            f"Task {t['id']}: difficulty={d!r} not in {sorted(VALID_DIFFICULTIES)}"
        )


def test_category_not_empty():
    data = _load()
    for t in data:
        cat = t.get("category", "")
        assert cat and isinstance(cat, str), (
            f"Task {t['id']}: category must be a non-empty string, got {cat!r}"
        )


def test_task_not_empty():
    data = _load()
    for t in data:
        desc = t.get("task", "")
        assert desc and isinstance(desc, str), (
            f"Task {t['id']}: task field must be a non-empty string, got {desc!r}"
        )


def test_expected_output_not_empty():
    data = _load()
    for t in data:
        out = t.get("expected_output")
        assert out is not None and str(out).strip() != "", (
            f"Task {t['id']}: expected_output must not be empty, got {out!r}"
        )


if __name__ == "__main__":
    tests = [
        test_json_loadable,
        test_exactly_20_tasks,
        test_ids_are_unique,
        test_required_fields_present,
        test_expected_failure_modes_is_list,
        test_difficulty_values_valid,
        test_category_not_empty,
        test_task_not_empty,
        test_expected_output_not_empty,
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
