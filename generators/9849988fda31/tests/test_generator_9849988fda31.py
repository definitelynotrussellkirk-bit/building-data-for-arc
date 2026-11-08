from __future__ import annotations

import copy
import importlib
import random

import pytest


GEN = importlib.import_module("puzzle_generators.per_puzzle.9849988fda31.generator")

CANONICAL_INPUTS = [
    [[4, 4, 4, 4, 4, 4], [8, 8, 8, 8, 8, 8]],
    [[3, 3, 3, 3, 3, 3], [9, 9, 9, 9, 9, 9]],
    [[6, 6, 6, 6, 6, 6], [2, 2, 2, 2, 2, 2]],
]


def _checker(grid):
    top, bottom = grid[0][0], grid[1][0]
    return [
        [top if (row + col) % 2 == 0 else bottom for col in range(len(grid[0]))]
        for row in range(2)
    ]


def test_canonical_inputs_are_accepted_and_strict():
    assert GEN.RULE_HASH == "961ad1f06f1a"
    for grid in CANONICAL_INPUTS:
        assert GEN.self_check(copy.deepcopy(grid)) == []
        assert GEN.strict_canonical_like(copy.deepcopy(grid)) == []


def test_generated_distribution_is_lawful_diverse_and_canonical_anchored():
    for band in ("easy", "medium", "hard"):
        widths = []
        strict_hits = 0
        for seed in range(200):
            grid = GEN.generate(seed, seed * 7 + 3, difficulty=band)
            assert GEN.self_check(grid) == []
            assert grid[0][0] != grid[1][0]
            assert all(value == grid[0][0] for value in grid[0])
            assert all(value == grid[1][0] for value in grid[1])
            widths.append(len(grid[0]))
            strict_hits += not GEN.strict_canonical_like(grid)
        assert strict_hits >= 20, (band, strict_hits)
        assert 6 in widths
        assert any(width != 6 for width in widths)
        assert len(set(widths)) >= 15


def test_exact_overrides_are_observable_and_boundaries_work():
    cases = (
        {"grid_w": 5, "stripe_color_a": 1, "stripe_color_b": 9},
        {"grid_w": 30, "stripe_color_a": 9, "stripe_color_b": 1},
        {"stripe_color_a": 5},
        {"stripe_color_b": 5},
    )
    for overrides in cases:
        grid = GEN.generate(17, 4, difficulty="hard", **overrides)
        observed = GEN.observe_overrides(grid)
        for axis, requested in overrides.items():
            assert observed[axis] == requested

    with pytest.raises(ValueError, match="stripe_color_a.*stripe_color_b"):
        GEN.generate(17, 4, stripe_color_a=4, stripe_color_b=4)
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(17, 4, typo_color=3)
    with pytest.raises(ValueError):
        GEN.generate(17, 4, grid_w=4)
    with pytest.raises(ValueError):
        GEN.generate(17, 4, stripe_color_a=0)


def test_self_check_rejects_targeted_rule_hiding_impostors():
    base = copy.deepcopy(CANONICAL_INPUTS[0])
    wrong_height = [base[0]]
    width_one = [[4], [8]]
    same_colors = [[4] * 6, [4] * 6]
    nonuniform_top = copy.deepcopy(base)
    nonuniform_top[0][3] = 8
    zero_role = [[0] * 6, [8] * 6]
    ragged = [[4] * 6, [8] * 5]

    for impostor in (
        wrong_height,
        width_one,
        same_colors,
        nonuniform_top,
        zero_role,
        ragged,
    ):
        assert GEN.self_check(impostor), impostor


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(90210)
    state = random.getstate()
    first = GEN.generate(23, 11, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(23, 11, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 0
    assert GEN.generate(23, 11, difficulty="medium") == second


def test_semantic_witnesses_refute_named_rivals_in_both_width_branches():
    canonical = GEN.generate(7, 2, grid_w=6, stripe_color_a=2, stripe_color_b=7)
    generalized = GEN.generate(7, 2, grid_w=17, stripe_color_a=2, stripe_color_b=7)
    assert GEN.SEMANTIC_WITNESSES["canonical_width_6"](canonical)
    assert GEN.SEMANTIC_WITNESSES["generalized_width"](generalized)

    for grid in (canonical, generalized):
        expected = _checker(grid)
        for rival in GEN.SEMANTIC_RIVALS.values():
            assert rival(grid) != expected


def test_lesson_identifiability_and_negative_recombination():
    grids = [
        GEN.generate(31, 0, grid_w=6, stripe_color_a=2, stripe_color_b=7),
        GEN.generate(31, 1, grid_w=11, stripe_color_a=5, stripe_color_b=1),
        GEN.generate(31, 2, grid_w=18, stripe_color_a=9, stripe_color_b=3),
    ]
    demos = [{"input": grid, "output": _checker(grid)} for grid in grids[:2]]
    assert GEN.lesson_identifiable(demos, {"input": grids[2], "output": _checker(grids[2])}) == []

    malformed = copy.deepcopy(grids[2])
    malformed[0][-1] = malformed[1][0]
    assert GEN.self_check(malformed)
    reasons = GEN.lesson_identifiable(demos, {"input": malformed})
    assert any("query input" in reason for reason in reasons)

    bad_demos = copy.deepcopy(demos)
    bad_demos[0]["output"] = GEN.SEMANTIC_RIVALS["copy_horizontal_stripes"](
        bad_demos[0]["input"]
    )
    reasons = GEN.lesson_identifiable(bad_demos, {"input": grids[2]})
    assert any("authoritative checker" in reason for reason in reasons)
