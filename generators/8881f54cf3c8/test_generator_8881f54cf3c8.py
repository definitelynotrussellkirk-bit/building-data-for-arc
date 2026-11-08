from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "8881f54cf3c8"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def test_canonical_pairs_are_accepted_and_match_selected_rule() -> None:
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_canonical_op3_pair_refutes_clean_boolean_shortcut() -> None:
    pair = next(pair for pair in canonical_pairs(TASK_ID) if pair["input"][0][0] == 3)
    assert GEN.rule_mirror(pair["input"]) == pair["output"]
    assert GEN._clean_boolean(pair["input"]) != pair["output"]
    assert len(pair["output"]) == 4
    assert len(pair["output"][0]) == 11


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 8, "grid_w": 13, "op": 1, "a_size": 4, "b_size": 4, "overlap_cells": 1},
        {"grid_h": 9, "grid_w": 14, "op": 2, "a_size": 6, "b_size": 6, "overlap_cells": 2},
        {"grid_h": 8, "grid_w": 14, "op": 3, "a_size": 5, "b_size": 6, "overlap_cells": 1},
        {"grid_h": 9, "grid_w": 13, "op": 4, "a_size": 6, "b_size": 4, "overlap_cells": 2},
    ],
)
def test_override_boundaries_are_exact_and_observable(overrides) -> None:
    grid = GEN.generate(7001, 19, difficulty="hard", **overrides)
    assert GEN.self_check(grid) == []
    observed = GEN.observe_overrides(grid)
    assert {key: observed[key] for key in overrides} == overrides


def test_unknown_override_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=3)


def test_self_check_rejects_targeted_structural_impostors() -> None:
    good = GEN.generate(9001, 0, difficulty="medium")
    assert GEN.self_check(good) == []

    ragged = copy.deepcopy(good)
    ragged[0].pop()
    bad_key = copy.deepcopy(good)
    bad_key[0][0] = 0
    key_band_polluted = copy.deepcopy(good)
    key_band_polluted[1][1] = 2

    for bad in (
        ragged,
        bad_key,
        key_band_polluted,
        GEN.generate(1, 0, texture="no_op"),
        GEN.generate(1, 0, texture="missing_color"),
        GEN.generate(1, 0, texture="identical_sets"),
    ):
        assert GEN.self_check(bad)


def test_replay_freshness_and_global_rng_purity() -> None:
    random.seed(123456)
    before = random.getstate()
    first = GEN.generate(42, 7, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(42, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    assert before == after


def test_every_four_demo_window_covers_branches_and_refutes_rivals() -> None:
    pairs = []
    for sample_index in range(16):
        grid = GEN.generate(8128, sample_index, difficulty="medium")
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    for start in range(0, 12):
        assert GEN.lesson_identifiable(pairs[start : start + 4], pairs[start + 4]) == []


def test_every_ordinary_op3_draw_exposes_key_participation() -> None:
    for seed in range(20):
        grid = GEN.generate(seed, 2, difficulty="hard")
        assert grid[0][0] == 3
        assert GEN.rule_mirror(grid) != GEN._clean_boolean(grid)


def test_negative_recombination_is_rejected_but_rule_still_executes() -> None:
    grid = GEN.generate(333, 0, difficulty="easy")
    bad = copy.deepcopy(grid)
    # Add a replacement feature (color 5) absent from every remaining scene part.
    bad[1][2] = 5
    assert GEN.self_check(bad)
    out = GEN.rule_mirror(bad)
    assert out and out[0]
