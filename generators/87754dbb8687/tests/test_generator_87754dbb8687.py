"""Focused regressions for the equality-matrix source generator."""
from __future__ import annotations

import importlib.util
import random
from pathlib import Path

import pytest


GENERATOR = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("generator_87754dbb8687", GENERATOR)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _headers(grid):
    return grid[0][1:], [row[0] for row in grid[1:]]


def test_exact_dimension_endpoints_work_in_every_difficulty_band():
    for difficulty in (None, "easy", "medium", "hard"):
        small = GEN.generate(7, 0, difficulty=difficulty, grid_h=4, grid_w=4)
        large = GEN.generate(7, 1, difficulty=difficulty, grid_h=10, grid_w=10)
        assert (len(small), len(small[0])) == (4, 4)
        assert (len(large), len(large[0])) == (10, 10)
        assert GEN.self_check(small) == []
        assert GEN.self_check(large) == []


def test_n_shared_and_distinct_color_controls_are_exact():
    no_shared = GEN.generate(
        11,
        2,
        grid_h=8,
        grid_w=9,
        n_shared=0,
        palette_size=8,
        n_distinct_colors=6,
    )
    top, left = _headers(no_shared)
    assert len(set(top) & set(left)) == 0
    assert len(set(top) | set(left)) == 6
    assert GEN.self_check(no_shared) == []

    four_shared = GEN.generate(
        11,
        3,
        grid_h=8,
        grid_w=9,
        n_shared=4,
        palette_size=8,
        n_distinct_colors=7,
    )
    top, left = _headers(four_shared)
    assert len(set(top) & set(left)) == 4
    assert len(set(top) | set(left)) == 7
    assert GEN.self_check(four_shared) == []


def test_nonzero_color_one_is_in_ordinary_generated_support():
    seen = set()
    for seed in range(64):
        grid = GEN.generate(seed, seed * 13 + 5, difficulty="medium")
        top, left = _headers(grid)
        seen.update(top)
        seen.update(left)
    assert 1 in seen


def test_rule_mirror_constructs_the_literal_equality_matrix():
    grid = [
        [0, 1, 4, 1, 7],
        [4, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [7, 0, 0, 0, 0],
    ]
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) == [
        [0, 4, 0, 0],
        [1, 0, 1, 0],
        [0, 0, 0, 7],
    ]


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261026)
    before = random.getstate()
    first = GEN.generate(91, 23, difficulty="hard")
    middle = random.getstate()
    second = GEN.generate(91, 23, difficulty="hard")
    after = random.getstate()
    assert before == middle == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_infeasible_exact_requests_and_unknown_controls_fail_loudly():
    with pytest.raises(ValueError, match="cannot realize"):
        GEN.generate(
            0,
            0,
            grid_h=4,
            grid_w=4,
            n_shared=0,
            n_distinct_colors=8,
            palette_size=8,
        )
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, typo_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="extreme")
