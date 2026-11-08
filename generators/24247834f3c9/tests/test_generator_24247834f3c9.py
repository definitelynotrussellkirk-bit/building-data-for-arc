"""Focused regression tests for generator 24247834f3c9."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.24247834f3c9.generator")
from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "24247834f3c9"


def test_canonical_pairs_are_accepted_and_python_mirror_matches() -> None:
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen._solve_official(pair["input"]) == pair["output"]


def test_exact_override_boundaries_are_realized() -> None:
    for grid_n in (10, 18):
        for seed_col in (1, 5):
            for fg_color in (1, 9):
                grid = gen.generate(
                    123,
                    7,
                    difficulty="hard",
                    grid_n=grid_n,
                    seed_col=seed_col,
                    fg_color=fg_color,
                )
                assert gen.self_check(grid) == []
                assert gen.observe_overrides(grid) == {
                    "grid_n": grid_n,
                    "seed_col": seed_col,
                    "fg_color": fg_color,
                }


def test_unknown_override_is_rejected_loudly() -> None:
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 2, typo_seed_column=3)


def test_self_check_rejects_four_structural_impostors() -> None:
    valid = gen.generate(99, 4, grid_n=10, seed_col=3, fg_color=7)

    second_seed = copy.deepcopy(valid)
    second_seed[-1][4] = 2
    assert any("exactly one" in error for error in gen.self_check(second_seed))

    moved_seed = copy.deepcopy(valid)
    moved_seed[-1][3] = 0
    moved_seed[-2][3] = 7
    assert any("bottom row" in error for error in gen.self_check(moved_seed))

    gray_seed = copy.deepcopy(valid)
    gray_seed[-1][3] = 5
    assert any("marker color 5" in error for error in gen.self_check(gray_seed))

    wrong_column = copy.deepcopy(valid)
    wrong_column[-1][3] = 0
    wrong_column[-1][6] = 7
    assert any("seed column" in error for error in gen.self_check(wrong_column))

    nonsquare = copy.deepcopy(valid)
    nonsquare.append([0] * 10)
    assert any("square" in error for error in gen.self_check(nonsquare))


def test_generation_is_deterministic_fresh_and_rng_pure() -> None:
    state_before = random.getstate()
    first = gen.generate(8128, 31, difficulty="medium")
    state_after = random.getstate()
    second = gen.generate(8128, 31, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert state_before == state_after


def test_named_semantic_rivals_are_refuted_by_every_lawful_draw() -> None:
    for seed in range(12):
        grid = gen.generate(seed, seed + 100, difficulty="easy")
        official = gen._solve_official(grid)
        for name, rival in gen.SEMANTIC_RIVALS.items():
            assert rival(grid) != official, name
        assert all(predicate(grid) for predicate in gen.SEMANTIC_WITNESSES.values())


def test_two_demo_episode_is_identifiable_against_named_competitors() -> None:
    grids = [gen.generate(501, index, difficulty="medium") for index in range(3)]
    pairs = [
        {"input": grid, "output": gen._solve_official(grid)}
        for grid in grids
    ]
    assert gen.lesson_identifiable(pairs[:2], pairs[2]) == []
