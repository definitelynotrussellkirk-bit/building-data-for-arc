from __future__ import annotations

import copy
import importlib
import random

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.7c21f478e6ac.generator")
from scripts.canonical_profile_gate import canonical_inputs


def test_canonical_inputs_are_accepted_and_rule_mirror_matches_known_shape():
    canonical = canonical_inputs(gen.TASK_ID)
    assert len(canonical) == 5
    assert all(gen.self_check(grid) == [] for grid in canonical)
    first = canonical[0]
    output = gen.rule_mirror(first)
    assert output[2][2] == 2
    assert output[1][2] == output[3][2] == output[2][1] == output[2][3] == 2


def test_exact_scene_profile_overrides_round_trip_in_every_band():
    for band in ("easy", "medium", "hard"):
        for index, profile in enumerate(gen.SCENE_PROFILES):
            grid = gen.generate(4100 + index, index, difficulty=band, scene_profile=profile)
            assert gen.self_check(grid, difficulty=band) == []
            assert gen.observe_overrides(grid) == {"scene_profile": profile}


def test_default_schedule_covers_every_profile_in_any_seven_consecutive_draws():
    for start in range(14):
        observed = {
            gen.observe_overrides(gen.generate(77, sample_index, difficulty="medium"))["scene_profile"]
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED)
        }
        assert observed == set(gen.SCENE_PROFILES)


def test_determinism_fresh_returns_and_global_random_state():
    state = random.getstate()
    a = gen.generate(123, 9, difficulty="hard")
    b = gen.generate(123, 9, difficulty="hard")
    assert a == b
    assert a is not b and all(x is not y for x, y in zip(a, b))
    a[0][0] = 9 if a[0][0] != 9 else 8
    assert a != b
    assert random.getstate() == state


def test_self_check_rejects_targeted_impostors():
    impostors = {
        "empty_background": [[0] * 7 for _ in range(7)],
        "adjacent_cells": [[0] * 7 for _ in range(7)],
        "output_like_plus": [[0] * 7 for _ in range(7)],
        "out_of_range_color": [[0] * 7 for _ in range(7)],
        "ragged": [[0] * 7, [0] * 6],
    }
    impostors["adjacent_cells"][2][2] = 3
    impostors["adjacent_cells"][2][3] = 4
    for r, c in ((3, 3), (2, 3), (4, 3), (3, 2), (3, 4)):
        impostors["output_like_plus"][r][c] = 5
    impostors["out_of_range_color"][1][1] = 10
    impostors["out_of_range_color"][5][5] = 2
    for name, grid in impostors.items():
        assert gen.self_check(grid), name


def test_unknown_and_invalid_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="edge_multicolor")
    with pytest.raises(ValueError, match="unknown scene_profile"):
        gen.generate(1, 0, scene_profile="not_a_profile")


def test_boundary_profile_refutes_canonical_shortcut():
    grid = gen.generate(91, 0, difficulty="easy", scene_profile="corner_multicolor")
    assert gen.CANONICAL_SHORTCUTS["ignore_boundary_seeds"](copy.deepcopy(grid)) != gen.rule_mirror(grid)


def test_seven_demo_lesson_refutes_all_declared_competitors():
    demos = []
    for index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(812, index, difficulty="medium")
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(812, gen.EXAMPLES_NEEDED, difficulty="medium")
    assert gen.lesson_identifiable(demos, {"input": query_grid}) == []
