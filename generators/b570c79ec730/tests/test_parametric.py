from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK = "b570c79ec730"
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


def test_default_program_is_exact_canonical_and_completion_is_distinct():
    p = load_prototype()
    preserve = p.program({"border_policy": "preserve_existing"})
    complete = p.program({"border_policy": "complete_bbox"})
    assert preserve == canonical_program()
    assert complete != preserve
    assert complete.strip().startswith("(rule!")


def test_controls_are_strict_and_bad_settings_are_rejected():
    p = load_prototype()
    good = {"border_policy": "preserve_existing"}
    for bad_seed in (True, 1.0, "1", -1, 2**63):
        with pytest.raises((TypeError, ValueError)):
            p.generate(bad_seed, good, 3, 4)
    for settings in ({}, {"border_policy": "erase_all"}, {"border_policy": "preserve_existing", "x": 1}):
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
    preserve = p.generate(23, {"border_policy": "preserve_existing"}, 3, 4)
    complete = p.generate(23, {"border_policy": "complete_bbox"}, 3, 4)
    assert all_inputs(preserve) == all_inputs(complete)
    assert len({json.dumps(g) for g in all_inputs(preserve)}) == 7
    assert all(a["output"] != b["output"] for a, b in zip(preserve["train"], complete["train"]))

    two = p.generate(23, {"border_policy": "preserve_existing"}, 2, 4)
    six = p.generate(23, {"border_policy": "preserve_existing"}, 6, 4)
    one_query = p.generate(23, {"border_policy": "preserve_existing"}, 3, 1)
    assert two["train"] == six["train"][:2]
    assert two["test"] == six["test"]
    assert one_query["train"] == preserve["train"]
    assert one_query["test"] == preserve["test"][:1]


def test_every_demo_has_a_missing_bbox_edge_witness_and_alternate_fills_it():
    p = load_prototype()
    preserve = p.generate(31, {"border_policy": "preserve_existing"}, 3, 4)
    complete = p.generate(31, {"border_policy": "complete_bbox"}, 3, 4)
    for left, right in zip(preserve["train"], complete["train"]):
        witnesses = p.missing_boundary_cells(left["input"])
        assert witnesses
        assert all(left["output"][r][c] == 0 for r, c, _ in witnesses)
        assert all(right["output"][r][c] == color for r, c, color in witnesses)


def test_queries_include_substantive_exact_30_by_30_and_python_labels():
    p = load_prototype()
    episode = p.generate(5, {"border_policy": "complete_bbox"}, 3, 4)
    dims = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert dims == [(8, 10), (16, 20), (23, 29), (30, 30)]
    large = episode["test"][-1]["input"]
    occupied = {(r, c) for r, row in enumerate(large) for c, value in enumerate(row) if value}
    assert len(occupied) >= 100
    assert {0, 29} <= {r for r, _ in occupied}
    assert {0, 29} <= {c for _, c in occupied}
    assert len({value for row in large for value in row if value}) >= 5
    for split in ("train", "test"):
        for pair in episode[split]:
            assert pair["output"] == p.apply_rule(pair["input"], "complete_bbox")


def test_public_first_turn_is_count_stable_and_structurally_hides_query_label():
    p = load_prototype()
    four = p.generate(13, {"border_policy": "complete_bbox"}, 3, 4)
    one = p.generate(13, {"border_policy": "complete_bbox"}, 3, 1)
    public_four = public_challenge_bytes(
        {"train": four["train"], "test": [{"input": four["test"][0]["input"]}]}
    )
    public_one = public_challenge_bytes(
        {"train": one["train"], "test": [{"input": one["test"][0]["input"]}]}
    )
    assert public_four == public_one
    assert b"complete_bbox" not in public_four
    assert b"program_solution" not in public_four
    projected = json.loads(public_four)
    assert set(projected["test"][0]) == {"input"}
