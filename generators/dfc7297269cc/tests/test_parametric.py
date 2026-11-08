"""Focused tests for the native parametric family of dfc7297269cc."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK = "dfc7297269cc"
TASK_ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = TASK_ROOT / "workspace" / "parametric" / "prototype.py"
PROMOTION = TASK_ROOT / "workspace" / "parametric" / "promotion.json"


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


def test_default_program_is_exact_canonical_and_ranked_rule_is_distinct():
    p = load_prototype()
    canonical = p.program({"completion": "horizontal_all"})
    ranked = p.program({"completion": "ranked_vertical"})
    assert canonical == canonical_program()
    assert ranked != canonical
    assert ranked.strip().startswith("(rule!")


def test_promotion_contract_declares_only_supported_counts_and_settings():
    data = json.loads(PROMOTION.read_text(encoding="utf-8"))
    assert data == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/dfc7297269cc/workspace/parametric/adapter.py",
        "parameters": {"completion": ["horizontal_all", "ranked_vertical"]},
        "default": {"completion": "horizontal_all"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            "generators/dfc7297269cc/workspace/parametric/prototype.py",
            "generators/dfc7297269cc/workspace/parametric/canonical.rkt",
            "generators/dfc7297269cc/workspace/parametric/ranked_vertical.rkt",
        ],
    }


def test_controls_are_strict_and_bad_settings_are_rejected():
    p = load_prototype()
    good = {"completion": "horizontal_all"}
    for bad_seed in (True, 1.0, "1", -1, 2**63):
        with pytest.raises((TypeError, ValueError)):
            p.generate(bad_seed, good, 3, 4)
    for settings in (
        {},
        {"completion": "unknown"},
        {"completion": "horizontal_all", "extra": 1},
        {"completion": True},
    ):
        with pytest.raises((TypeError, ValueError)):
            p.generate(0, settings, 3, 4)
    for demos in (1, 7, True, 3.0):
        with pytest.raises((TypeError, ValueError)):
            p.generate(0, good, demos, 4)
    for queries in (0, 5, True, 4.0):
        with pytest.raises((TypeError, ValueError)):
            p.generate(0, good, 3, queries)


def test_inputs_are_setting_neutral_distinct_and_prefix_stable():
    p = load_prototype()
    canonical = p.generate(41, {"completion": "horizontal_all"}, 3, 4)
    ranked = p.generate(41, {"completion": "ranked_vertical"}, 3, 4)
    assert all_inputs(canonical) == all_inputs(ranked)
    assert len({json.dumps(grid) for grid in all_inputs(canonical)}) == 7
    assert all(a["output"] != b["output"] for a, b in zip(canonical["train"], ranked["train"]))

    two = p.generate(41, {"completion": "horizontal_all"}, 2, 4)
    six = p.generate(41, {"completion": "horizontal_all"}, 6, 4)
    one_query = p.generate(41, {"completion": "horizontal_all"}, 3, 1)
    assert two["train"] == six["train"][:2]
    assert two["test"] == six["test"]
    assert one_query["train"] == canonical["train"]
    assert one_query["test"] == canonical["test"][:1]


def test_two_demonstrations_identify_both_settings_and_refute_declared_rivals():
    p = load_prototype()
    for seed in range(16):
        canonical = p.generate(seed, {"completion": "horizontal_all"}, 2, 4)
        ranked = p.generate(seed, {"completion": "ranked_vertical"}, 2, 4)
        assert p.surviving_rivals(canonical["train"], "horizontal_all") == []
        assert p.surviving_rivals(ranked["train"], "ranked_vertical") == []
        assert all(a["output"] != b["output"] for a, b in zip(canonical["train"], ranked["train"]))


def test_queries_cover_four_profiles_and_substantive_exact_30_by_30():
    p = load_prototype()
    episode = p.generate(5, {"completion": "ranked_vertical"}, 3, 4)
    dims = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert dims == [(15, 17), (20, 22), (25, 27), (30, 30)]
    large = episode["test"][-1]["input"]
    occupied = {(r, c) for r, row in enumerate(large) for c, value in enumerate(row) if value}
    assert len(occupied) >= 55
    assert {0, 29} <= {r for r, _ in occupied}
    assert {0, 29} <= {c for _, c in occupied}
    assert len({value for row in large for value in row if value}) == 9

    for split in ("train", "test"):
        for pair in episode[split]:
            grid = pair["input"]
            horizontal = p.horizontal_centers(grid)
            vertical = p.vertical_centers(grid)
            assert 1 <= len(horizontal) <= 4
            assert len(vertical) == 6
            assert pair["output"] == p.apply_rule(grid, "ranked_vertical")


def test_wrong_intermediate_changes_the_final_output():
    p = load_prototype()
    episode = p.generate(7, {"completion": "ranked_vertical"}, 3, 4)
    grid = episode["test"][0]["input"]  # profile rank is three
    assert len(p.horizontal_centers(grid)) == 3
    correct = p.apply_rule(grid, "ranked_vertical")
    wrong = p.apply_with_vertical_rank(grid, 1)
    assert correct != wrong
    assert p.changed_cells(correct, wrong) == 2


def test_public_first_turn_is_count_stable_and_hides_private_values():
    p = load_prototype()
    four = p.generate(13, {"completion": "ranked_vertical"}, 3, 4)
    one = p.generate(13, {"completion": "ranked_vertical"}, 3, 1)
    public_four = public_challenge_bytes(
        {"train": four["train"], "test": [{"input": four["test"][0]["input"]}]}
    )
    public_one = public_challenge_bytes(
        {"train": one["train"], "test": [{"input": one["test"][0]["input"]}]}
    )
    assert public_four == public_one
    assert b"ranked_vertical" not in public_four
    assert b"program_solution" not in public_four
    projected = json.loads(public_four)
    assert set(projected["test"][0]) == {"input"}
