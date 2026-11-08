"""Portable semantic regressions; component/count logic is independent of the generator."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import random

import pytest
from reviewer_support import canonical_pairs, find_root


TASK = "4f1ec6a61342"
ROOT = find_root(__file__)
GENERATOR_PATH = ROOT / "generators" / TASK / "generator.py"
if not GENERATOR_PATH.is_file():
    GENERATOR_PATH = ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("reviewed_chambers", GENERATOR_PATH)
generator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(generator)


def chambers(grid):
    """Cardinal components excluding walls and the control, in scan order."""
    height, width = len(grid), len(grid[0])
    visited = {(0, 0)}
    result = []
    for row in range(height):
        for column in range(width):
            if (row, column) in visited or grid[row][column] == 5:
                continue
            pending = [(row, column)]
            visited.add((row, column))
            cells = []
            while pending:
                r, c = pending.pop()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in visited and grid[nr][nc] != 5):
                        visited.add((nr, nc))
                        pending.append((nr, nc))
            result.append(cells)
    return result


def seed_count(grid, cells):
    return sum(grid[r][c] == 2 for r, c in cells)


def prediction(grid, rule="exact_count"):
    regions = chambers(grid)
    target = grid[0][0]
    counts = [seed_count(grid, cells) for cells in regions]
    if rule in ("ordinal_rank", "clamped_ordinal_rank"):
        order = sorted(range(len(regions)), key=lambda i: counts[i])
        index = min(target, len(order) - 1) if rule == "clamped_ordinal_rank" else target
        selected = order[index:index + 1]
    elif rule == "distinct_seed_columns":
        selected = [i for i, cells in enumerate(regions)
                    if len({c for r, c in cells if grid[r][c] == 2}) == target]
    else:
        effective_target = min(target, 3) if rule == "clipped_control" else target
        selected = [i for i, count in enumerate(counts) if count == effective_target]
    output = [[5 if value == 5 else 0 for value in row] for row in grid]
    for index in selected:
        for r, c in regions[index]:
            output[r][c] = 8
    return output


RIVALS = ("ordinal_rank", "clamped_ordinal_rank", "distinct_seed_columns", "clipped_control")


def assert_valid(grid, expected_chambers=None):
    assert isinstance(grid, list) and grid and all(isinstance(row, list) for row in grid)
    assert len({len(row) for row in grid}) == 1 and grid[0]
    assert all(type(value) is int for row in grid for value in row)
    assert 1 <= grid[0][0] <= 6
    height, width = len(grid), len(grid[0])
    for r in range(height):
        for c in range(width):
            if (r, c) == (0, 0):
                continue
            assert grid[r][c] in (0, 2, 5)
            if r in (0, height - 1) or c in (0, width - 1):
                assert grid[r][c] == 5
    regions = chambers(grid)
    assert 2 <= len(regions) <= 6
    if expected_chambers is not None:
        assert len(regions) == expected_chambers
    for cells in regions:
        min_r, max_r = min(r for r, c in cells), max(r for r, c in cells)
        min_c, max_c = min(c for r, c in cells), max(c for r, c in cells)
        assert len(cells) == (max_r - min_r + 1) * (max_c - min_c + 1)
    assert sum(seed_count(grid, cells) == grid[0][0] for cells in regions) == 1
    assert generator.self_check(grid) == []
    return regions


@pytest.mark.parametrize("grid", [
    [], [[]], [[1, 5], [5]], [[True, 5], [5, 0]], [[1, 5], [5, "2"]],
    [[1.0, 5], [5, 2]], [[1, 5], [5, 9]], [[1, 5], [5, -1]],
    [[1, 5], [5, 2]], [[2, 5, 5], [5, 0, 5], [5, 5, 5]],
])
def test_selfcheck_rejects_malformed_and_false_target_grids(grid):
    errors = generator.self_check(grid)
    assert isinstance(errors, list) and errors


def test_selfcheck_rejects_missing_and_duplicate_target():
    grid = generator.generate(19, 0, grid_h=13, grid_w=15, n_chambers=4, target_count=2)
    regions = assert_valid(grid, 4)
    target = next(cells for cells in regions if seed_count(grid, cells) == 2)
    missing = [row[:] for row in grid]
    for r, c in target:
        missing[r][c] = 0
    assert generator.self_check(missing)
    duplicate = [row[:] for row in grid]
    other = next(cells for cells in regions if cells != target and len(cells) >= 2)
    for r, c in other:
        duplicate[r][c] = 0
    for r, c in other[:2]:
        duplicate[r][c] = 2
    assert generator.self_check(duplicate)


def test_adjacent_divider_regression():
    assert_valid(generator.generate(0, 5, n_chambers=3), 3)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_seed_sweep_is_valid(band):
    for index in range(40):
        assert_valid(generator.generate(17, index, difficulty=band))


@pytest.mark.parametrize("number", range(2, 7))
def test_explicit_chamber_count_is_observable(number):
    for seed in range(4):
        assert_valid(generator.generate(seed, 5, grid_h=13, grid_w=15,
                                        n_chambers=number, target_count=3), number)


@pytest.mark.parametrize("height", range(7, 19))
def test_height_domain(height):
    grid = generator.generate(7, 0, grid_h=height, grid_w=15, n_chambers=4, target_count=3)
    assert len(grid) == height
    assert_valid(grid, 4)


@pytest.mark.parametrize("width", range(9, 21))
def test_width_domain(width):
    grid = generator.generate(7, 0, grid_h=13, grid_w=width, n_chambers=4, target_count=3)
    assert len(grid[0]) == width
    assert_valid(grid, 4)


@pytest.mark.parametrize("target", range(1, 7))
def test_control_domain(target):
    grid = generator.generate(23, 0, grid_h=13, grid_w=15, n_chambers=4, target_count=target)
    assert grid[0][0] == target
    assert_valid(grid, 4)
    assert prediction(grid)[0][0] == (5 if target == 5 else 0)


@pytest.mark.parametrize("number", range(2, 7))
@pytest.mark.parametrize("target", range(1, 7))
def test_minimum_dimensions_joint_capacity(number, target):
    grid = generator.generate(11, 5, grid_h=7, grid_w=9,
                              n_chambers=number, target_count=target)
    assert (len(grid), len(grid[0])) == (7, 9)
    assert grid[0][0] == target
    assert_valid(grid, number)


@pytest.mark.parametrize("overrides", [
    {"unknown_axis": 1}, {"palette_kind": "nonsense"},
    {"grid_h": True}, {"grid_h": "10"}, {"grid_w": 12.5},
    {"n_chambers": False}, {"target_count": "2"},
    {"grid_h": 6}, {"grid_h": 19}, {"grid_w": 8}, {"grid_w": 21},
    {"n_chambers": 1}, {"n_chambers": 7}, {"target_count": 0}, {"target_count": 7},
])
def test_override_names_types_and_bounds_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(0, 0, **overrides)


def test_four_observable_axes():
    assert set(generator.AXES) == {"grid_h", "grid_w", "n_chambers", "target_count"}
    grid = generator.generate(3, 0, grid_h=17, grid_w=19, n_chambers=5, target_count=6)
    assert (len(grid), len(grid[0]), len(chambers(grid)), grid[0][0]) == (17, 19, 5, 6)
    assert_valid(grid, 5)


def test_canonical_grids_are_accepted_and_oracle_matches_recorded_outputs():
    pairs = canonical_pairs(TASK, root=find_root(__file__))
    assert pairs
    for pair in pairs:
        assert_valid(pair["input"], 4)
        assert prediction(pair["input"]) == pair["output"]


def test_canonical_shortcuts_have_verified_fit_and_declared_names():
    pairs = canonical_pairs(TASK, root=find_root(__file__))
    for name in RIVALS:
        assert name in generator.CANONICAL_SHORTCUTS
        assert name in generator.LESSON_COMPETITORS
        for pair in pairs:
            assert prediction(pair["input"], name) == pair["output"]
            assert generator.CANONICAL_SHORTCUTS[name](pair["input"]) == pair["output"]


def test_default_lessons_refute_canonical_fitting_rivals():
    for band in ("easy", "medium", "hard"):
        grids = [generator.generate(31, index, difficulty=band) for index in range(18)]
        for index, grid in enumerate(grids):
            regions = assert_valid(grid)
            if index % 2 == 0:
                assert 4 <= grid[0][0] <= 6
                assert 2 <= len(regions) <= 4
                target_cells = next(cells for cells in regions
                                    if seed_count(grid, cells) == grid[0][0])
                assert len({c for r, c in target_cells if grid[r][c] == 2}) < grid[0][0]
                assert any(seed_count(grid, cells) > grid[0][0]
                           for cells in regions if cells != target_cells)
                for name in RIVALS:
                    assert prediction(grid, name) != prediction(grid)
        for start in range(len(grids) - 3):
            demos = grids[start:start + 3]
            for name in RIVALS:
                assert any(prediction(grid, name) != prediction(grid) for grid in demos)
        assert any(len(chambers(grid)) == 4 and grid[0][0] <= 3
                   and sorted(seed_count(grid, cells) for cells in chambers(grid)) == [0, 1, 2, 3]
                   for grid in grids[1::2])


def test_generation_is_deterministic_and_does_not_touch_global_rng():
    random.seed(901)
    before = random.getstate()
    first = generator.generate(44, 7, difficulty="hard")
    assert random.getstate() == before
    random.seed(902)
    before = random.getstate()
    second = generator.generate(44, 7, difficulty="hard")
    assert random.getstate() == before
    assert first == second


def test_teaching_target_has_no_fixed_second_largest_rank():
    higher_counts = set()
    for index in range(0, 200, 2):
        grid = generator.generate(17, index, difficulty="medium")
        regions = chambers(grid)
        if len(regions) >= 3:
            higher_counts.add(sum(seed_count(grid, room) > grid[0][0] for room in regions))
    assert {1, 2} <= higher_counts
