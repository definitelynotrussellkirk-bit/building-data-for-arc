"""Regressions for unique-largest-green lesson coverage and validation."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
sys.path.insert(0, str(REPO / "shared/runtime"))
spec = importlib.util.spec_from_file_location(
    "stamp_generator_largest_green_under_test", HOME / "generator.py"
)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def _color_components(grid, color):
    height, width = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] == color
    }
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    cells.add(nxt)
                    stack.append(nxt)
        result.append(cells)
    return sorted(result, key=lambda cells: (-len(cells), min(cells)))


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_default_three_example_window_exercises_largest_green_selection(band):
    for seed in range(12):
        grids = [gen.generate(seed, index, difficulty=band) for index in range(3)]
        green_components = [_color_components(grid, 3) for grid in grids]
        assert any(len(parts) == 2 for parts in green_components), (band, seed)
        for parts in green_components:
            assert len(parts[0]) in (3, 4, 5)
            assert all(len(part) == 1 for part in parts[1:])


def test_rule_mirror_uses_unique_largest_green_component_and_preserves_distractor():
    grid = [[0] * 10 for _ in range(8)]
    grid[0][8] = 3  # smaller green distractor
    grid[1][1] = grid[2][1] = grid[2][2] = 3  # unique largest template
    grid[5][5] = 1
    expected = [row[:] for row in grid]
    expected[6][5] = expected[6][6] = 1

    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == expected


def test_self_check_rejects_stamp_footprint_that_overwrites_green_distractor():
    grid = [[0] * 10 for _ in range(8)]
    grid[1][1] = grid[2][1] = grid[2][2] = 3  # L-shaped reference
    grid[5][5] = 3  # smaller green distractor
    grid[4][4] = 1  # L stamp would write through the distractor at (5, 5)

    reasons = gen.self_check(grid)

    assert any("overlaps" in reason for reason in reasons), reasons


def test_mutation_fixtures_include_green_distractor_stamp_collision():
    fixtures = dict(gen.mutation_fixtures())

    assert "green_distractor_in_stamp" in fixtures
    reasons = gen.self_check(fixtures["green_distractor_in_stamp"])
    assert any("overlaps" in reason for reason in reasons), reasons
