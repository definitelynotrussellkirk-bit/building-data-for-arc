from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK = "cc74d7392ecd"
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


def inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_canonical_and_alternate_is_distinct():
    p = load_prototype()
    default = p.program({"neighborhood": "orthogonal"})
    alternate = p.program({"neighborhood": "diagonal"})
    assert default == canonical_program()
    assert alternate != default
    assert alternate.strip().startswith("(rule!")


def test_generate_rejects_coercible_controls_and_bad_settings():
    p = load_prototype()
    good = {"neighborhood": "orthogonal"}
    for bad_seed in (True, 1.0, "1", -1, 2**63):
        with pytest.raises((TypeError, ValueError)):
            p.generate(bad_seed, good, 3, 4)
    for bad_settings in ({}, {"neighborhood": "square"}, {"neighborhood": "orthogonal", "x": 1}):
        with pytest.raises((TypeError, ValueError)):
            p.generate(0, bad_settings, 3, 4)
    for demos in (1, 7, True, 3.0):
        with pytest.raises((TypeError, ValueError)):
            p.generate(0, good, demos, 4)
    for queries in (0, 5, True, 4.0):
        with pytest.raises((TypeError, ValueError)):
            p.generate(0, good, 3, queries)


def test_inputs_are_setting_neutral_distinct_and_count_prefix_stable():
    p = load_prototype()
    orth = p.generate(17, {"neighborhood": "orthogonal"}, 3, 4)
    diag = p.generate(17, {"neighborhood": "diagonal"}, 3, 4)
    assert inputs(orth) == inputs(diag)
    assert len({json.dumps(grid) for grid in inputs(orth)}) == 7
    assert all(a["output"] != b["output"] for a, b in zip(orth["train"], diag["train"]))

    two = p.generate(17, {"neighborhood": "orthogonal"}, 2, 4)
    six = p.generate(17, {"neighborhood": "orthogonal"}, 6, 4)
    one_query = p.generate(17, {"neighborhood": "orthogonal"}, 3, 1)
    assert two["train"] == six["train"][:2]
    assert two["test"] == six["test"]
    assert one_query["train"] == orth["train"]
    assert one_query["test"] == orth["test"][:1]


def test_four_queries_cover_minimum_large_and_substantive_30_by_30_scenes():
    p = load_prototype()
    episode = p.generate(3, {"neighborhood": "orthogonal"}, 3, 4)
    dims = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert dims == [(7, 7), (16, 20), (23, 29), (30, 30)]
    large = episode["test"][-1]["input"]
    occupied = {(r, c) for r, row in enumerate(large) for c, value in enumerate(row) if value}
    assert len(occupied) >= 20
    assert {0, 29} <= {r for r, _ in occupied}
    assert {0, 29} <= {c for _, c in occupied}
    assert len({value for row in large for value in row if value}) >= 5


def test_outputs_equal_python_rule_and_public_first_turn_hides_private_data():
    p = load_prototype()
    four = p.generate(9, {"neighborhood": "diagonal"}, 3, 4)
    one = p.generate(9, {"neighborhood": "diagonal"}, 3, 1)
    for split in ("train", "test"):
        for pair in four[split]:
            assert pair["output"] == p.apply_rule(pair["input"], "diagonal")

    first_four = public_challenge_bytes(
        {"train": four["train"], "test": [{"input": four["test"][0]["input"]}]}
    )
    first_one = public_challenge_bytes(
        {"train": one["train"], "test": [{"input": one["test"][0]["input"]}]}
    )
    assert first_four == first_one
    assert b"diagonal" not in first_four
    assert b"program_solution" not in first_four
    assert json.dumps(four["test"][0]["output"], separators=(",", ":")).encode() not in first_four
