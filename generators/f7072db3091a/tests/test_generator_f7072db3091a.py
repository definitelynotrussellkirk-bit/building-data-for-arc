"""Focused regression tests for generator f7072db3091a."""
from __future__ import annotations

import random

import pytest

from puzzle_generators.per_puzzle.f7072db3091a import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def _valid_minimal_grid() -> list[list[int]]:
    grid = [[0] * 8 for _ in range(8)]
    grid[0][0:3] = [1, 1, 1]
    for row in range(5, 8):
        grid[row][7] = 1
    grid[3][3] = 5
    return grid


def test_canonical_inputs_are_accepted() -> None:
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    assert [gen.self_check(pair["input"]) for pair in pairs] == [[]] * 5


def test_exact_overrides_are_observable_at_boundaries() -> None:
    for overrides in (
        {"grid_h": 8, "grid_w": 8, "n_lines": 4, "marker_count": 2},
        {"grid_h": 20, "grid_w": 20, "n_lines": 2, "marker_count": 1},
    ):
        grid = gen.generate(91, 17, difficulty="hard", **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid, meta={"overrides": overrides}) == []


def test_unknown_override_is_rejected() -> None:
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 0, misspelled_axis=3)


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(1107)
    state_before = random.getstate()
    first = gen.generate(12345, 77, difficulty="medium")
    state_after = random.getstate()
    second = gen.generate(12345, 77, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert state_before == state_after


def test_self_check_rejects_targeted_impostors() -> None:
    no_marker = _valid_minimal_grid()
    no_marker[3][3] = 0

    one_orientation = [[0] * 8 for _ in range(8)]
    one_orientation[0][0:3] = [1, 1, 1]
    one_orientation[2][2:6] = [1, 1, 1, 1]
    one_orientation[4][4] = 5

    bent = _valid_minimal_grid()
    bent[1][2] = 1

    singleton = _valid_minimal_grid()
    singleton[3][0] = 1

    illegal_palette = _valid_minimal_grid()
    illegal_palette[4][4] = 9

    cases = {
        "missing marker": no_marker,
        "single orientation": one_orientation,
        "bent component": bent,
        "singleton component": singleton,
        "illegal palette": illegal_palette,
    }
    for name, grid in cases.items():
        assert gen.self_check(grid), name


def test_each_declared_rival_is_killed_by_an_ordinary_draw() -> None:
    grid = gen.generate(808, 3, difficulty="easy")
    official = gen._oracle(grid)
    assert gen.strict_canonical_like(grid) == []
    for name, rival in gen.SEMANTIC_RIVALS.items():
        assert rival(grid) != official, name
