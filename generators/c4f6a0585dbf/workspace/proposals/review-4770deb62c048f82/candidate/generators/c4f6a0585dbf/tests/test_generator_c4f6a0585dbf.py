"""Focused regressions for the selected c4f6a0585dbf generator."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from reviewer_support import find_root, load_selected_generator

TASK_ID = "c4f6a0585dbf"
ROOT = find_root(Path(__file__))
gen, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _recolor_port_cells(grid: list[list[int]], color: int) -> list[list[int]]:
    recolored = deepcopy(grid)
    for row in recolored:
        for index, value in enumerate(row):
            if value == 4:
                row[index] = color
    return recolored


@pytest.mark.parametrize(
    "override",
    [
        {"palette_kind": "warm"},
        {"palette_kind": "cool"},
        {"texture": "warm"},
        {"texture": "primary"},
    ],
)
def test_rejects_palette_aliases_outside_literal_color_four_authority(override):
    """The canonical Racket program only recognizes literal marker color 4."""
    with pytest.raises(ValueError, match=r"(?:literal|port).*4|4.*(?:literal|port)"):
        gen.generate(13, 5, difficulty="medium", **override)


@pytest.mark.parametrize("replacement", [2, 3, 7, 8])
def test_self_check_rejects_recolored_port_cells(replacement):
    """A recolored trigger must not remain inside the documented generator domain."""
    canonical = gen.generate(13, 5, difficulty="medium")
    recolored = _recolor_port_cells(canonical, replacement)
    errors = gen.self_check(recolored)
    assert any("port color" in error and "4" in error for error in errors), errors


def test_default_and_declared_degenerate_draws_keep_literal_color_four():
    for seed in range(12):
        grid = gen.generate(seed, seed * 17 + 5, difficulty="medium")
        colors = {value for row in grid for value in row}
        assert colors <= {0, 1, 4}
        assert 4 in colors
        assert gen.self_check(grid) == []

    no_targets = gen.generate(0, 0, texture="no_targets")
    assert {value for row in no_targets for value in row} == {0, 1, 4}
    assert gen.self_check(no_targets) == []


def test_self_check_rejects_non_full_grid_without_literal_color_four_ports():
    grid = [[0 for _ in range(23)] for _ in range(23)]
    for row in range(10, 13):
        for col in range(10, 14):
            grid[row][col] = 1

    errors = gen.self_check(grid)

    assert any("missing literal color-4 ports" in error for error in errors), errors


def test_no_targets_degenerate_still_requires_two_or_three_ports():
    grid = gen.generate(0, 0, texture="no_targets")
    grid[11][12] = 1

    errors = gen.self_check(grid)

    assert any("2..3 ports" in error for error in errors), errors


def test_self_check_rejects_port_on_template_boundary():
    grid = gen.generate(0, 0, texture="no_targets")
    grid[11][11] = 1
    grid[10][11] = 4

    errors = gen.self_check(grid)

    assert any("strictly interior" in error for error in errors), errors


def test_self_check_rejects_non_port_hole_inside_template_bbox():
    grid = [[0 for _ in range(23)] for _ in range(23)]
    for row in range(9, 14):
        for col in range(9, 14):
            grid[row][col] = 1
    grid[10][10] = 4
    grid[10][12] = 4
    grid[12][11] = 0

    errors = gen.self_check(grid)

    assert any("non-port holes" in error for error in errors), errors
