"""Observe exact controls from pixels, independently of generator metadata.

These tests describe the selected multicolor training manifold. Monochrome
grids can still be lawful inputs to the pure Racket reflection operation.
"""
from __future__ import annotations

import importlib.util
import sys

import pytest

from reviewer_support import find_root


TASK_ID = "57488f2a7c15"
ROOT = find_root(__file__)
BANDS = ("easy", "medium", "hard")
INTEGER_BOUNDS = {
    "side": (4, 16),
    "n_cells": (2, 12),
    "n_distinct_colors": (2, 9),
    "n_diagonal": (0, 3),
    "n_pairs": (0, 3),
}


@pytest.fixture(scope="module")
def generator():
    candidates = (ROOT / "generators" / TASK_ID / "generator.py",
                  ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py")
    source = next(path for path in candidates if path.is_file())
    spec = importlib.util.spec_from_file_location("symmetry_override_generator", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def observe(grid):
    assert isinstance(grid, list) and grid
    side = len(grid)
    assert all(isinstance(row, list) and len(row) == side for row in grid)
    assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)
    assert all(grid[r][c] == 0 or grid[c][r] == 0 or grid[r][c] == grid[c][r]
               for r in range(side) for c in range(r + 1, side))
    unpaired = [(r, c) for r in range(side) for c in range(side)
                if r != c and grid[r][c] != 0 and grid[c][r] == 0]
    assert unpaired, "selected training examples must require a visible completion"
    orientation = ("lower" if all(r > c for r, c in unpaired) else
                   "upper" if all(r < c for r, c in unpaired) else "mixed")
    return {
        "side": side,
        "n_cells": sum(cell != 0 for row in grid for cell in row),
        "n_distinct_colors": len({cell for row in grid for cell in row if cell != 0}),
        "n_diagonal": sum(grid[i][i] != 0 for i in range(side)),
        "n_pairs": sum(grid[r][c] != 0 and grid[c][r] != 0
                       for r in range(side) for c in range(r + 1, side)),
        "source_triangle": orientation,
    }


def controls(side, cells, colors, diagonal, pairs, triangle):
    return {"side": side, "n_cells": cells, "n_distinct_colors": colors,
            "n_diagonal": diagonal, "n_pairs": pairs, "source_triangle": triangle}


JOINT_CASES = [
    controls(4, 2, 2, 0, 0, "lower"),
    controls(4, 2, 2, 0, 0, "upper"),
    controls(4, 2, 2, 0, 0, "mixed"),
    controls(5, 5, 4, 1, 0, "lower"),
    controls(4, 12, 9, 3, 3, "lower"),
    controls(4, 12, 9, 3, 3, "upper"),
    controls(4, 12, 9, 3, 3, "mixed"),
    controls(16, 12, 9, 0, 3, "mixed"),
    controls(16, 12, 9, 3, 0, "upper"),
    controls(4, 7, 4, 0, 3, "lower"),
    controls(4, 4, 4, 3, 0, "upper"),
    controls(7, 7, 2, 2, 1, "mixed"),
]


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("requested", JOINT_CASES)
def test_feasible_joint_controls_are_exact(generator, band, requested):
    for seed in (0, 17):
        grid = generator.generate(seed=seed, sample_index=seed, difficulty=band, **requested)
        assert observe(grid) == requested, (band, seed, requested, grid)
        assert generator.self_check(grid, difficulty=band) == [], (band, requested, grid)


SINGLE_CASES = [(axis, value) for axis, bounds in INTEGER_BOUNDS.items() for value in bounds]
SINGLE_CASES.extend(("source_triangle", value) for value in ("lower", "upper", "mixed"))


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("axis,value", SINGLE_CASES)
def test_feasible_single_control_boundaries_are_exact(generator, band, axis, value):
    for seed in (0, 1, 7):
        grid = generator.generate(seed=seed, sample_index=seed, difficulty=band, **{axis: value})
        observed = observe(grid)
        assert observed[axis] == value, (band, seed, axis, value, observed)
        assert generator.self_check(grid, difficulty=band) == [], (band, seed, grid)


@pytest.mark.parametrize("requested", [
    controls(4, 7, 2, 0, 0, "lower"),  # seven distinct off-diagonal orbits do not fit
    controls(5, 2, 3, 0, 0, "lower"),  # more colors than occupied cells
    controls(5, 4, 4, 0, 1, "lower"),  # an equal-colored pair uses one color slot
    controls(5, 2, 2, 2, 0, "lower"),  # only diagonal cells: no completion
    controls(5, 4, 2, 0, 2, "lower"),  # only completed pairs: no completion
    controls(5, 3, 2, 2, 0, "mixed"),  # one unpaired source cannot use both triangles
    controls(5, 3, 2, 0, 1, "mixed"),
    controls(5, 2, 2, 3, 0, "upper"),  # more diagonal cells than total cells
    controls(5, 2, 2, 0, 2, "upper"),  # more pair cells than total cells
])
def test_infeasible_joint_controls_raise_structured_error(generator, requested):
    with pytest.raises(ValueError) as raised:
        generator.generate(seed=17, sample_index=17, difficulty="medium", **requested)
    axes = getattr(raised.value, "incompatible_axes", None)
    assert isinstance(axes, (tuple, list)) and axes
    assert all(isinstance(axis, str) for axis in axes)
    assert set(axes) <= set(requested)


@pytest.mark.parametrize("axis", INTEGER_BOUNDS)
@pytest.mark.parametrize("value", [True, 4.0, "4"])
def test_integer_controls_reject_coercion(generator, axis, value):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(seed=0, sample_index=0, difficulty="medium", **{axis: value})


@pytest.mark.parametrize("axis,value", [(axis, value) for axis, (lo, hi) in INTEGER_BOUNDS.items()
                                      for value in (lo - 1, hi + 1)])
def test_integer_controls_reject_out_of_range_values(generator, axis, value):
    with pytest.raises(ValueError):
        generator.generate(seed=0, sample_index=0, difficulty="medium", **{axis: value})


def test_unknown_control_is_rejected(generator):
    with pytest.raises(ValueError):
        generator.generate(seed=0, sample_index=0, difficulty="medium", unknown_axis=1)


@pytest.mark.parametrize("value", ["diagonal", "", 1, True])
def test_invalid_triangle_is_rejected(generator, value):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(seed=0, sample_index=0, difficulty="medium", source_triangle=value)
