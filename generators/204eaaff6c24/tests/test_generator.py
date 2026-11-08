"""Regression tests for the selected 204eaaff6c24 generator repair.

The canonical Racket rule remains label authority.  These tests cover the
input sampler, strict public API, declared semantic rival, and lesson schedule.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

TASK_HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py"))


def _load_generator(path: Path = GENERATOR_PATH):
    spec = importlib.util.spec_from_file_location("generator_204eaaff6c24_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()

CANONICAL_PAIRS = (
    (
        [[0, 7, 0], [0, 0, 0], [0, 0, 0]],
        [[7]],
    ),
    (
        [[0, 2, 0], [2, 0, 0], [0, 2, 0]],
        [[2, 2, 2]],
    ),
    (
        [[0, 8, 0], [8, 8, 0], [8, 0, 0]],
        [[8, 8, 8, 8]],
    ),
    (
        [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
        [[1, 1]],
    ),
    (
        [[4, 4, 0], [4, 0, 4], [0, 0, 4]],
        [[4, 4, 4, 4, 4]],
    ),
)


def intended_output(grid):
    colors = {value for row in grid for value in row if value != 0}
    assert len(colors) == 1
    color = next(iter(colors))
    count = sum(value == color for row in grid for value in row)
    return [[color] * count]


def component_sizes_8(grid):
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    sizes = []
    while cells:
        todo = [cells.pop()]
        size = 0
        while todo:
            r, c = todo.pop()
            size += 1
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == dc == 0:
                        continue
                    neighbor = (r + dr, c + dc)
                    if neighbor in cells:
                        cells.remove(neighbor)
                        todo.append(neighbor)
        sizes.append(size)
    return sorted(sizes, reverse=True)


@pytest.mark.parametrize("grid,expected", CANONICAL_PAIRS)
def test_canonical_examples_are_accepted_and_match_independent_count_oracle(grid, expected):
    assert GEN.self_check(grid) == []
    assert intended_output(grid) == expected


@pytest.mark.parametrize(
    "args,kwargs",
    [
        ((True, 0), {}),
        ((1.5, 0), {}),
        (("1", 0), {}),
        ((0, True), {}),
        ((0, -1), {}),
        ((0, 1.5), {}),
        ((0, 0), {"difficulty": "expert"}),
        ((0, 0), {"difficulty": 0.5}),
        ((0, 0), {"typo_axis": 3}),
        ((0, 0), {"n_cells": True}),
        ((0, 0), {"n_cells": 3.0}),
        ((0, 0), {"n_cells": "3"}),
        ((0, 0), {"grid_h": False}),
        ((0, 0), {"grid_w": 4.0}),
        ((0, 0), {"fg_color": True}),
        ((0, 0), {"fg_color": 4.0}),
        ((0, 0), {"fg_color": "4"}),
        ((0, 0), {"fg_layout": 3}),
        ((0, 0), {"texture": False}),
    ],
)
def test_invalid_call_scalars_and_overrides_are_rejected(args, kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(*args, **kwargs)


@pytest.mark.parametrize(
    "layout,axis",
    [("row", "grid_w"), ("column", "grid_h"), ("diagonal", "both")],
)
def test_free_dimensions_grow_to_honor_large_layout_specific_count(layout, axis):
    grid = GEN.generate(17, 9, difficulty="easy", fg_layout=layout, n_cells=12)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid)["n_cells"] == 12
    h, w = len(grid), len(grid[0])
    if axis in ("grid_h", "both"):
        assert h >= 12
    if axis in ("grid_w", "both"):
        assert w >= 12


def test_infeasible_exact_layout_overrides_are_structured_conflicts():
    with pytest.raises(ValueError) as caught:
        GEN.generate(0, 0, grid_h=3, grid_w=3, n_cells=8, fg_layout="row")
    assert set(getattr(caught.value, "incompatible_axes", ())) == {
        "fg_layout", "grid_h", "grid_w", "n_cells"
    }


def test_layout_alias_conflict_is_declared_and_structured():
    assert any(set(entry) == {"fg_layout", "texture"} for entry in GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS)
    with pytest.raises(ValueError) as caught:
        GEN.generate(0, 0, fg_layout="row", texture="column")
    assert set(getattr(caught.value, "incompatible_axes", ())) == {"fg_layout", "texture"}


def test_schedule_repeats_and_every_four_pair_window_has_two_rival_witnesses():
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    expected_profiles = tuple(GEN.SCHEDULE_PROFILES)
    assert len(expected_profiles) == 4
    assert [GEN.schedule_profile(5, index, "hard") for index in range(8)] == list(expected_profiles) * 2

    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(500 + index, index, difficulty=band) for index in range(12)]
        for start in range(9):
            window = grids[start:start + 4]
            witness_count = sum(len(component_sizes_8(grid)) >= 2 for grid in window)
            assert witness_count >= 2, (band, start, witness_count)
            for held_out in range(4):
                demos = [grid for index, grid in enumerate(window) if index != held_out]
                assert any(len(component_sizes_8(grid)) >= 2 for grid in demos)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_deterministic_schedule_meets_strict_canonical_profile_floor(band):
    grids = [GEN.generate(1100 + index, index, difficulty=band) for index in range(20)]
    exact = [grid for grid in grids if (len(grid), len(grid[0]), len({v for row in grid for v in row if v})) == (3, 3, 1)]
    assert len(exact) >= 5


def test_declared_largest_component_rival_fits_canonical_and_has_lawful_witness():
    rival = GEN.SEMANTIC_RIVALS["largest_8_connected_component"]
    for grid, expected in CANONICAL_PAIRS:
        assert rival(grid) == expected

    witness = [[4, 0, 0], [0, 0, 0], [0, 0, 4]]
    assert GEN.self_check(witness) == []
    assert GEN.SEMANTIC_WITNESSES["multiple_8_connected_components"](witness)
    assert intended_output(witness) == [[4, 4]]
    assert rival(witness) == [[4]]
    assert GEN.WITNESS_RIVALS["multiple_8_connected_components"] == [
        "largest_8_connected_component"
    ]


def test_default_generation_is_deterministic_lawful_and_observable():
    for band in (None, "easy", "medium", "hard"):
        for seed in range(15):
            for sample_index in range(8):
                first = GEN.generate(seed, sample_index, difficulty=band)
                second = GEN.generate(seed, sample_index, difficulty=band)
                assert first == second
                assert GEN.self_check(first, difficulty=band) == []
                observed = GEN.observe_overrides(first)
                assert 1 <= observed["fg_color"] <= 9
                assert 1 <= observed["n_cells"] <= 30
