"""Pixel-level regressions for the horizontal-mirror stamping contract.

Canonical data is authoring evidence, read through the portable public helper.
The measuring code below does not call any generator geometry or output helper.
"""
from __future__ import annotations

import importlib.util
from itertools import product
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root


TASK = "f1668de79fa1"
ROOT = find_root(__file__)
SOURCE = Path(__file__).resolve().parents[1] / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("selected_mirror_stamp_generator", SOURCE)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gen
SPEC.loader.exec_module(gen)

AXES = {"grid_h", "grid_w", "template_cells", "marker_mode"}
BANDS = (None, "easy", "medium", "hard")
CANONICAL = canonical_pairs(TASK, root=ROOT)


def cells_of(grid, color):
    return {(r, c) for r, row in enumerate(grid) for c, cell in enumerate(row)
            if cell == color}


def stamp_pixels(grid):
    """Derive the visible mirrored stamp using absolute source coordinates."""
    source = cells_of(grid, 2)
    top = min(r for r, _ in source)
    right = max(c for _, c in source)
    marker_r, marker_c = next(iter(cells_of(grid, 1)))
    h, w = len(grid), len(grid[0])
    return {(marker_r + r - top, marker_c + right - c)
            for r, c in source
            if 0 <= marker_r + r - top < h
            and 0 <= marker_c + right - c < w}


def observed_pixels(grid):
    count = len(cells_of(grid, 2))
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "template_cells": count,
            "marker_mode": "full" if len(stamp_pixels(grid)) == count else "clipped"}


def assert_lawful_pixels(grid):
    assert isinstance(grid, list) and grid
    assert all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
    assert all(type(cell) is int and cell in (0, 1, 2) for row in grid for cell in row)
    assert len(cells_of(grid, 1)) == 1
    source = cells_of(grid, 2)
    assert 4 <= len(source) <= 9
    reached = {next(iter(source))}
    frontier = list(reached)
    while frontier:
        r, c = frontier.pop()
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in source and neighbor not in reached:
                reached.add(neighbor)
                frontier.append(neighbor)
    assert reached == source, "the color-2 template must be 4-connected"
    assert stamp_pixels(grid), "clipping must leave at least one output cell"


def hand_grid(marker=(0, 4)):
    """An independently specified L tetromino on the minimum 6-by-8 canvas."""
    grid = [[0] * 8 for _ in range(6)]
    for r, c in ((1, 1), (2, 1), (3, 1), (3, 2)):
        grid[r][c] = 2
    grid[marker[0]][marker[1]] = 1
    return grid


def test_only_genuine_pixel_observable_axes_are_advertised():
    assert set(gen.AXES) == AXES


@pytest.mark.parametrize("pair", CANONICAL,
                         ids=lambda p: f"v{p['variant']}-{p['split']}-{p['pair_index']}")
def test_all_canonical_inputs_are_accepted_and_match_independent_stamp(pair):
    grid = pair["input"]
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert stamp_pixels(grid) == cells_of(pair["output"], 8)
    assert all(cell in (0, 8) for row in pair["output"] for cell in row)
    assert gen.observe_overrides(grid) == observed_pixels(grid)


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("h,w,count,mode", list(product((6, 18), (8, 22), (4, 9),
                                                      ("full", "clipped"))))
def test_joint_axis_boundaries_are_realized_and_lawful(band, h, w, count, mode):
    requested = dict(grid_h=h, grid_w=w, template_cells=count, marker_mode=mode)
    grid = gen.generate(731, 5, difficulty=band, **requested)
    assert observed_pixels(grid) == requested
    assert_lawful_pixels(grid)
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize("count", range(4, 10))
@pytest.mark.parametrize("mode", ("full", "clipped"))
def test_every_template_count_is_feasible_on_the_smallest_canvas(count, mode):
    requested = dict(grid_h=6, grid_w=8, template_cells=count, marker_mode=mode)
    grid = gen.generate(192, count, **requested)
    assert observed_pixels(grid) == requested
    assert_lawful_pixels(grid)


@pytest.mark.parametrize("overrides", [
    {"grid_h": 5}, {"grid_h": 19}, {"grid_h": True}, {"grid_h": 6.0},
    {"grid_h": "6"}, {"grid_h": None},
    {"grid_w": 7}, {"grid_w": 23}, {"grid_w": False}, {"grid_w": 8.0},
    {"grid_w": "8"}, {"grid_w": None},
    {"template_cells": 3}, {"template_cells": 10}, {"template_cells": True},
    {"template_cells": 4.0}, {"template_cells": "4"}, {"template_cells": None},
    {"marker_mode": ""}, {"marker_mode": "FULL"}, {"marker_mode": "partial"},
    {"marker_mode": 0}, {"marker_mode": False}, {"marker_mode": None},
    {"marker_mode": []}, {"marker_mode": {}},
])
def test_bad_axis_values_fail_loudly_with_value_error(overrides):
    with pytest.raises(ValueError):
        gen.generate(8, 2, **overrides)


@pytest.mark.parametrize("overrides", [
    {"misspelled_axis": 4}, {"height": 6}, {"width": 8},
    {"palette_kind": "warm"}, {"palette_size": 2},
    {"position_bias": "template_with_marker"}, {"n_distinct_colors": 2},
    {"density": "sparse"}, {"texture": "default"},
])
def test_unknown_and_retired_inert_controls_are_rejected(overrides):
    with pytest.raises(ValueError):
        gen.generate(8, 2, **overrides)


@pytest.mark.parametrize("marker,expected", [
    ((0, 4), {(0, 5), (1, 5), (2, 4), (2, 5)}),
    ((4, 6), {(4, 7), (5, 7)}),
])
def test_observer_and_validators_accept_hand_derived_full_and_clipped_stamps(marker, expected):
    grid = hand_grid(marker)
    assert stamp_pixels(grid) == expected
    assert_lawful_pixels(grid)
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert gen.observe_overrides(grid) == observed_pixels(grid)


@pytest.mark.parametrize("checker", ("self_check", "strict_canonical_like"))
@pytest.mark.parametrize("bad_cell", (False, 0.0, "0", None, -1, 3, 8, 10))
def test_validators_reject_malformed_or_extraneous_cells(checker, bad_cell):
    grid = hand_grid()
    grid[0][0] = bad_cell
    errors = getattr(gen, checker)(grid)
    assert isinstance(errors, list) and errors
    assert all(isinstance(error, str) for error in errors)


@pytest.mark.parametrize("checker", ("self_check", "strict_canonical_like"))
@pytest.mark.parametrize("grid", (None, [], [[]], [None], [[0], [0, 0]]))
def test_validators_return_reasons_for_malformed_grid_structure(checker, grid):
    errors = getattr(gen, checker)(grid)
    assert isinstance(errors, list) and errors
    assert all(isinstance(error, str) for error in errors)


@pytest.mark.parametrize("checker", ("self_check", "strict_canonical_like"))
@pytest.mark.parametrize("case", ("missing_marker", "second_marker", "missing_template",
                                  "disconnected_template", "empty_stamp"))
def test_validators_reject_semantically_invalid_scenes(checker, case):
    grid = hand_grid((5, 7) if case == "empty_stamp" else (0, 4))
    if case == "missing_marker":
        grid[0][4] = 0
    elif case == "second_marker":
        grid[5][7] = 1
    elif case == "missing_template":
        grid = [[0 if cell == 2 else cell for cell in row] for row in grid]
    elif case == "disconnected_template":
        grid[5][0] = 2
    if case == "empty_stamp":
        assert stamp_pixels(grid) == set()
    errors = getattr(gen, checker)(grid)
    assert isinstance(errors, list) and errors


@pytest.mark.parametrize("band", BANDS)
def test_generation_is_deterministic_lawful_and_returns_fresh_grids(band):
    for index in range(12):
        first = gen.generate(314159, index, difficulty=band)
        saved = [row[:] for row in first]
        assert first == gen.generate(314159, index, difficulty=band)
        assert_lawful_pixels(first)
        observed = observed_pixels(first)
        assert 6 <= observed["grid_h"] <= 18
        assert 8 <= observed["grid_w"] <= 22
        assert gen.observe_overrides(first) == observed
        assert gen.self_check(first) == []
        assert gen.strict_canonical_like(first) == []
        first[0][0] = 99
        assert gen.generate(314159, index, difficulty=band) == saved
