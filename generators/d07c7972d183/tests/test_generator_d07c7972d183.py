from __future__ import annotations

import copy
import importlib
import random

import pytest
from reviewer_support import canonical_pairs, find_root


TASK_ID = "d07c7972d183"
MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.d07c7972d183.generator"
)


def _canonical_inputs():
    return [pair["input"] for pair in canonical_pairs(TASK_ID, root=find_root(__file__))]


def _component_count(grid, color=1):
    seen = set()
    components = 0
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            components += 1
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                rr, cc = stack.pop()
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
    return components


def test_canonical_inputs_are_accepted():
    assert len(_canonical_inputs()) == 4
    for grid in _canonical_inputs():
        assert MODULE.self_check(grid) == []


def test_default_draws_are_binary_periodic_and_observable():
    periods = set()
    shapes = set()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for seed in range(80):
            grid = MODULE.generate(seed + 1000 * band_index, seed * 7, difficulty=band)
            assert MODULE.self_check(grid) == []
            observed = MODULE.observe_overrides(grid)
            assert observed["grid_h"] == len(grid)
            assert observed["grid_w"] == len(grid[0])
            periods.add(observed["period"])
            shapes.add((len(grid), len(grid[0])))
    assert periods.issuperset({2, 3, 4})
    assert len(shapes) >= 12


def test_boundary_overrides_are_exact_or_loud():
    for case in (
        {"grid_h": 4},
        {"grid_h": 18},
        {"grid_w": 3},
        {"grid_w": 12},
        {"period": 2},
        {"period": 6},
        {"grid_h": 4, "period": 2, "grid_w": 3},
        {"grid_h": 18, "period": 6, "grid_w": 12},
    ):
        grid = MODULE.generate(5, 9, difficulty="easy", **case)
        observed = MODULE.observe_overrides(grid)
        for key, value in case.items():
            assert observed[key] == value
    with pytest.raises(ValueError, match="requires grid_h"):
        MODULE.generate(5, 9, grid_h=4, period=6)


def test_self_check_rejects_targeted_impostors():
    impostors = [
        [[0] * 3 for _ in range(6)],
        [[1] * 3 for _ in range(6)],
        [[0, 2, 0], [1, 0, 1]] * 3,
        [[0, 1, 0], [1, 0, 1], [0, 1, 1], [1, 1, 0], [0, 0, 1], [1, 0, 0]],
        [[0, 1, 0]],
        [[0, 0], [0, 0]],
    ]
    single_foreground_row = [[0] * 7 for _ in range(6)]
    single_background_row = [[1] * 7 for _ in range(6)]
    for row in (0, 3):
        single_foreground_row[row] = [0, 1, 1, 1, 1, 0, 0]
        single_background_row[row] = [1, 0, 0, 0, 0, 1, 1]
    impostors.extend((single_foreground_row, single_background_row))
    assert all(MODULE.self_check(grid) for grid in impostors)


def test_disconnected_foreground_branch_has_positive_support():
    witnesses = []
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for seed in range(400):
            grid = MODULE.generate(50_000 + 1000 * band_index + seed, seed, difficulty=band)
            if _component_count(grid) > 1:
                witnesses.append((band, seed))
                break
    assert {band for band, _ in witnesses} == {"easy", "medium", "hard"}


def test_replay_freshness_input_purity_and_global_rng():
    state = random.getstate()
    first = MODULE.generate(123, 7, difficulty="medium")
    assert random.getstate() == state
    frozen = copy.deepcopy(first)
    second = MODULE.generate(123, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 1 - first[0][0]
    third = MODULE.generate(123, 7, difficulty="medium")
    assert third == frozen
