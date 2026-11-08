from __future__ import annotations

from copy import deepcopy

import importlib

gen = importlib.import_module("puzzle_generators.per_puzzle.1ec2e9f43682.generator")


def test_canonical_inputs_are_accepted_and_mirrored():
    canonical = [
        [[5,5,5,5,5,5,5],[5,2,0,5,3,0,5],[5,0,0,5,0,0,5],[5,5,5,5,5,5,5]],
        [[5,5,5,5,5,5,5,5],[5,4,0,0,5,6,0,5],[5,0,0,0,5,0,0,5],[5,5,5,5,5,5,5,5]],
        [[5,5,5,5,5,5,5,5,5],[5,7,0,0,5,8,0,0,5],[5,0,0,0,5,0,0,0,5],[5,0,0,0,5,0,0,0,5],[5,5,5,5,5,5,5,5,5]],
    ]
    for grid in canonical:
        before = deepcopy(grid)
        assert gen.self_check(grid) == []
        output = gen.rule_mirror(grid)
        assert grid == before
        assert output != grid
        assert all(0 not in row for row in output)


def test_exact_overrides_are_observable_at_boundaries():
    cases = [
        dict(grid_h=4, grid_w=13, n_chambers=6, layout="vertical_strip", texture="top_left_seeds"),
        dict(grid_h=13, grid_w=4, n_chambers=6, layout="horizontal_strip", texture="varied_seeds"),
        dict(grid_h=22, grid_w=22, n_chambers=2, layout="vertical_strip", texture="varied_seeds"),
    ]
    for index, case in enumerate(cases):
        grid = gen.generate(1700 + index, 91 + index, difficulty="hard", **case)
        assert gen.observe_overrides(grid) == case
        assert gen.self_check(grid, meta={"overrides": case}) == []


def test_self_check_rejects_targeted_impostors():
    base = gen.generate(
        31, 7, difficulty="easy", grid_h=4, grid_w=7,
        n_chambers=2, layout="vertical_strip", texture="top_left_seeds",
    )

    missing_border = deepcopy(base)
    missing_border[0][1] = 0
    assert any("border" in error for error in gen.self_check(missing_border))

    missing_seed = deepcopy(base)
    missing_seed[1][1] = 0
    assert any("0 seeds" in error for error in gen.self_check(missing_seed))

    multiple_seeds = deepcopy(base)
    multiple_seeds[2][1] = 9
    assert any("2 seeds" in error for error in gen.self_check(multiple_seeds))

    broken_separator = deepcopy(base)
    _grid, features, errors = gen._scene_analysis(broken_separator)
    assert errors == []
    separator_col = features["rooms"][0]["bbox"][3] + 1
    broken_separator[1][separator_col] = 0
    assert gen.self_check(broken_separator)

    no_zero = deepcopy(base)
    _grid, features, errors = gen._scene_analysis(no_zero)
    assert errors == []
    room = features["rooms"][0]
    color = room["marker"][2]
    for r, c in room["cells"]:
        no_zero[r][c] = color
    assert any("no zero" in error for error in gen.self_check(no_zero))


def test_determinism_fresh_returns_and_rng_isolation():
    import random

    state = random.getstate()
    first = gen.generate(1234, 56, difficulty="medium")
    second = gen.generate(1234, 56, difficulty="medium")
    assert first == second
    assert first is not second
    first[0][0] = 0
    assert second[0][0] == 5
    assert random.getstate() == state


def test_canonical_schedule_has_disjoint_generalized_witnesses():
    canonical = [gen.generate(seed, 10, difficulty="hard") for seed in range(12)]
    assert all(gen.is_canonical_profile(grid) for grid in canonical)
    generalized = [gen.generate(seed, 11, difficulty="hard") for seed in range(12)]
    assert any(not gen.is_canonical_profile(grid) for grid in generalized)
    assert any(gen.observe_overrides(grid)["layout"] == "horizontal_strip" for grid in generalized)


def test_same_seed_sample_is_band_distinct():
    grids = [
        gen.generate(100000, 0, difficulty=band)
        for band in (None, "easy", "medium", "hard")
    ]
    frozen = {tuple(tuple(row) for row in grid) for grid in grids}
    assert len(frozen) == 4
