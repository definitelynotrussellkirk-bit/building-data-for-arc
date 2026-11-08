from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.fb413112b7c8 import generator as gen

ROOT = Path(__file__).resolve().parents[1]


def _canonical_inputs():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                pairs = list(row["train"]) + [row["test"]]
                return [pair["input"] for pair in pairs]
    raise AssertionError("canonical task row missing")


def _rigid_output(grid):
    analysis = gen._analyze(grid)
    assert not analysis["errors"]
    out = gen._blank_with_support(grid)
    delta = analysis["support_row"] - 1 - max(
        r for r, _, _ in analysis["colored"]
    )
    for r, c, value in analysis["colored"]:
        out[r + delta][c] = value
    return out


def test_rule_hash_and_canonical_inputs_are_accepted():
    assert gen.RULE_HASH == "881504b5004d"
    canonical = _canonical_inputs()
    assert len(canonical) == 3
    assert all(gen.self_check(grid) == [] for grid in canonical)
    assert all(gen.strict_canonical_like(grid) == [] for grid in canonical)


def test_boundary_override_tuple_is_exact_and_replayable():
    overrides = {
        "grid_h": 8,
        "grid_w": 8,
        "palette_kind": "warm",
        "total_cells": 8,
        "n_pieces": 3,
        "n_distinct_colors": 3,
        "gap_rows": 5,
        "support_inset": 3,
    }
    grid = gen.generate(41, 7, difficulty="hard", **overrides)
    replay = gen.generate(41, 7, difficulty="hard", **overrides)
    assert grid == replay
    assert grid is not replay
    assert all(a is not b for a, b in zip(grid, replay))
    observed = gen.observe_overrides(grid)
    assert observed == {key: value for key, value in overrides.items() if key != "palette_kind"}
    assert gen.self_check(grid) == []


def test_unknown_override_is_rejected_and_global_rng_is_untouched():
    random.seed(123456)
    state = random.getstate()
    gen.generate(3, 2, difficulty="medium")
    assert random.getstate() == state
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(3, 2, mystery_axis=7)


def test_self_check_rejects_rule_hiding_mutations():
    grid = gen.generate(13, 1, difficulty="medium")
    analysis = gen._analyze(grid)
    sr = analysis["support_row"]

    no_support = copy.deepcopy(grid)
    no_support[sr] = [0] * len(no_support[sr])
    assert any("support row" in error for error in gen.self_check(no_support))

    no_blob = copy.deepcopy(grid)
    for r, c, _ in analysis["colored"]:
        no_blob[r][c] = 0
    assert any("no droppable" in error for error in gen.self_check(no_blob))

    no_gap = copy.deepcopy(grid)
    r, c, value = max(analysis["colored"])
    no_gap[r][c] = 0
    no_gap[sr - 1][c] = value
    assert any("gap row" in error for error in gen.self_check(no_gap))

    stray_nine = copy.deepcopy(grid)
    stray_nine[0][0] = 9
    assert any("outside" in error or "exactly one" in error for error in gen.self_check(stray_nine))

    split_support = copy.deepcopy(grid)
    support_cols = analysis["support_cols"]
    split_support[sr][support_cols[len(support_cols) // 2]] = 0
    assert any("contiguous" in error for error in gen.self_check(split_support))


def test_schedule_makes_every_four_demo_window_identifiable():
    profiles = [gen.schedule_profile(0, i) for i in range(8)]
    for start in range(4):
        window = profiles[start : start + gen.EXAMPLES_NEEDED]
        assert "joint_counterexample_a" in window
        assert "joint_counterexample_b" in window

    for start in range(4):
        pairs = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(900 + start, sample_index, difficulty="medium")
            pairs.append({"input": grid, "output": _rigid_output(grid)})
        assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_control_profile_refutes_named_canonical_shortcuts():
    grid = gen.generate(77, 1, difficulty="easy")
    expected = _rigid_output(grid)
    assert gen.SEMANTIC_WITNESSES["unequal_component_bottoms"](grid)
    assert gen.SEMANTIC_WITNESSES["multiple_colors_preserved"](grid)
    assert gen.SEMANTIC_WITNESSES["small_low_component_refutes_largest_only"](grid)
    for name in (
        "independent_component_drop",
        "modal_color_only",
        "largest_component_only",
    ):
        assert gen.CANONICAL_SHORTCUTS[name](grid) != expected
