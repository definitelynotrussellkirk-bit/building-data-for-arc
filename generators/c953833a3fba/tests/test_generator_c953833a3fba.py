from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


TASK_ID = "c953833a3fba"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _demo(grid):
    return {"input": copy.deepcopy(grid), "output": gen.rule_mirror(grid)}


def test_rule_hash_and_python_mirror_match_all_canonical_pairs():
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID) == "2c7f294c8da4"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_self_check_rejects_four_targeted_structural_impostors():
    blank = [[0] * 9 for _ in range(9)]
    too_many = [[0] * 9 for _ in range(9)]
    for r, c in ((2, 2), (2, 4), (4, 2), (4, 4), (6, 6)):
        too_many[r][c] = 2
    ragged = [[0] * 9 for _ in range(9)]
    ragged[4] = ragged[4][:-1]
    too_small = [[0] * 4 for _ in range(4)]
    too_small[2][2] = 2
    short_line = [[0] * 9 for _ in range(9)]
    short_line[4][3:6] = [2, 2, 2]
    solid_2x2 = [[0] * 9 for _ in range(9)]
    for r, c in ((4, 4), (4, 5), (5, 4), (5, 5)):
        solid_2x2[r][c] = 2

    assert gen.self_check(blank)
    assert gen.self_check(too_many)
    assert gen.self_check(ragged)
    assert gen.self_check(too_small)
    assert gen.self_check(short_line)
    assert gen.self_check(solid_2x2)


def test_unknown_override_is_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, difficulty="easy", typo_axis=7)


def test_exact_override_boundaries_round_trip_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        for grid_h in (7, 18):
            for grid_w in (7, 18):
                for n_centers in (1, 4):
                    grid = gen.generate(
                        121,
                        1,
                        difficulty=difficulty,
                        grid_h=grid_h,
                        grid_w=grid_w,
                        n_centers=n_centers,
                    )
                    assert gen.observe_overrides(grid) == {
                        "grid_h": grid_h,
                        "grid_w": grid_w,
                        "n_centers": n_centers,
                    }
                    assert gen.strict_canonical_like(grid) == []


def test_close_centers_discriminate_union_distance_from_independent_rings():
    grid = [[0] * 9 for _ in range(9)]
    grid[4][2] = 2
    grid[4][5] = 2  # L1 separation 3: one center suppresses part of the other's ring.

    correct = gen.rule_mirror(grid)
    rival = gen.SEMANTIC_RIVALS["independent_center_rings"](grid)
    assert correct != rival
    assert correct[4][4] == 0  # distance 2 from left seed, but distance 1 from right seed.
    assert rival[4][4] == 8
    assert gen.SEMANTIC_WITNESSES["close_centers_require_union_distance"](grid)


def test_every_sliding_three_demo_window_is_identifiable():
    # The schedule is periodic with exactly EXAMPLES_NEEDED slots, so checking
    # multiple consecutive starts proves every residue class of the period.
    for difficulty in ("easy", "medium", "hard"):
        for start in range(9):
            grids = [gen.generate(500 + i, start + i, difficulty=difficulty) for i in range(4)]
            profiles = {
                gen.schedule_profile(0, start + i, difficulty)
                for i in range(gen.EXAMPLES_NEEDED)
            }
            assert profiles == set(gen.SCHEDULE_PROFILES)
            demos = [_demo(grid) for grid in grids[: gen.EXAMPLES_NEEDED]]
            query = {"input": grids[gen.EXAMPLES_NEEDED]}
            assert gen.lesson_identifiable(demos, query) == []


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(8675309)
    before = random.getstate()
    first = gen.generate(777, 13, difficulty="hard")
    after = random.getstate()
    second = gen.generate(777, 13, difficulty="hard")

    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))

    first[0][0] = 9
    third = gen.generate(777, 13, difficulty="hard")
    assert third == second


def test_canonical_shortcuts_only_contains_canonical_fitting_rules():
    assert gen.CANONICAL_SHORTCUTS == {}


def test_color_generalization_schedule_actually_exercises_cyan_centers():
    grids = [gen.generate(seed, 2, difficulty="medium") for seed in range(12)]
    assert any(any(value == 8 for row in grid for value in row) for grid in grids)
