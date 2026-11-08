from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK = "d1dd527dba87"
TASK_ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = TASK_ROOT / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    assert PROTOTYPE.is_file(), f"missing parametric prototype: {PROTOTYPE}"
    spec = importlib.util.spec_from_file_location(f"_{TASK}_parametric_test", PROTOTYPE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    root = find_root(__file__)
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row["program_solution"]
    raise AssertionError(f"missing canonical task {TASK}")


def all_inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_canonical_and_smallest_is_distinct():
    p = load_prototype()
    largest = p.program({"selector": "largest"})
    smallest = p.program({"selector": "smallest"})
    assert largest == canonical_program()
    assert smallest != largest
    assert smallest.strip().startswith("(rule!")


def test_controls_are_strict_and_bad_settings_are_rejected():
    p = load_prototype()
    good = {"selector": "largest"}
    for bad_seed in (True, 1.0, "1", -1, 2**63):
        with pytest.raises((TypeError, ValueError)):
            p.generate(bad_seed, good, 3, 4)
    for settings in ({}, {"selector": "middle"}, {"selector": "largest", "x": 1}):
        with pytest.raises((TypeError, ValueError)):
            p.generate(0, settings, 3, 4)
    for demos in (1, 7, True, 3.0):
        with pytest.raises((TypeError, ValueError)):
            p.generate(0, good, demos, 4)
    for queries in (0, 5, True, 4.0):
        with pytest.raises((TypeError, ValueError)):
            p.generate(0, good, 3, queries)


def test_inputs_are_setting_neutral_distinct_prefix_stable_and_identifying():
    p = load_prototype()
    largest = p.generate(41, {"selector": "largest"}, 3, 4)
    smallest = p.generate(41, {"selector": "smallest"}, 3, 4)
    assert all_inputs(largest) == all_inputs(smallest)
    assert len({json.dumps(g) for g in all_inputs(largest)}) == 7
    assert all(a["output"] != b["output"] for a, b in zip(largest["train"], smallest["train"]))

    two = p.generate(41, {"selector": "largest"}, 2, 4)
    six = p.generate(41, {"selector": "largest"}, 6, 4)
    one_query = p.generate(41, {"selector": "largest"}, 3, 1)
    assert two["train"] == six["train"][:2]
    assert two["test"] == six["test"]
    assert one_query["train"] == largest["train"]
    assert one_query["test"] == largest["test"][:1]


def test_three_demos_reverse_absolute_position_shortcuts_for_both_colors():
    p = load_prototype()
    episode = p.generate(7, {"selector": "largest"}, 3, 4)
    for color in (1, 2):
        row_relations = []
        col_relations = []
        for pair in episode["train"]:
            comps = sorted(p.components(pair["input"], color), key=len)
            small, large = comps[0], comps[-1]
            row_relations.append(min(r for r, _ in large) < min(r for r, _ in small))
            col_relations.append(min(c for _, c in large) < min(c for _, c in small))
        assert set(row_relations) == {False, True}
        assert set(col_relations) == {False, True}


def test_queries_include_substantive_exact_30_by_30_and_python_labels():
    p = load_prototype()
    episode = p.generate(5, {"selector": "smallest"}, 3, 4)
    dims = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert dims == [(9, 12), (16, 20), (23, 29), (30, 30)]
    large = episode["test"][-1]["input"]
    occupied = {(r, c) for r, row in enumerate(large) for c, value in enumerate(row) if value}
    assert len(occupied) >= 20
    assert {0, 29} <= {r for r, _ in occupied}
    assert {0, 29} <= {c for _, c in occupied}
    assert len({value for row in large for value in row if value}) >= 5
    for split in ("train", "test"):
        for pair in episode[split]:
            assert pair["output"] == p.apply_rule(pair["input"], "smallest")


def test_public_first_turn_is_count_stable_and_hides_private_values():
    p = load_prototype()
    four = p.generate(13, {"selector": "smallest"}, 3, 4)
    one = p.generate(13, {"selector": "smallest"}, 3, 1)
    public_four = public_challenge_bytes(
        {"train": four["train"], "test": [{"input": four["test"][0]["input"]}]}
    )
    public_one = public_challenge_bytes(
        {"train": one["train"], "test": [{"input": one["test"][0]["input"]}]}
    )
    assert public_four == public_one
    assert b"smallest" not in public_four
    assert b"program_solution" not in public_four
    projected = json.loads(public_four)
    assert set(projected["test"][0]) == {"input"}
