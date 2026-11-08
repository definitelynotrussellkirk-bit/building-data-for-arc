"""Regressions for the reviewed normalized-largest-component generator."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("_generator_729429f8ea2c", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator():
    return _load_generator()


def _components(grid, color):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = set()
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = (rr + dr, cc + dc)
                    if (0 <= nxt[0] < height and 0 <= nxt[1] < width
                            and nxt not in seen and grid[nxt[0]][nxt[1]] == color):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append(cells)
    return result


def _normalized(cells):
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return {(r - top, c - left) for r, c in cells}


def test_unknown_and_removed_palette_overrides_are_rejected(generator):
    with pytest.raises(ValueError, match="unknown override"):
        generator.generate(123, 7, difficulty="medium", definitely_not_an_axis="x")
    with pytest.raises(ValueError, match="unknown override"):
        generator.generate(123, 7, difficulty="medium", palette_kind="warm")


@pytest.mark.parametrize("difficulty", [None, "medium"])
def test_normal_samples_teach_unique_largest_component_selection(generator, difficulty):
    for seed in range(8):
        grid = generator.generate(seed, 0, difficulty=difficulty)
        assert generator.self_check(grid, difficulty=difficulty) == []
        for color in (2, 3):
            components = _components(grid, color)
            assert len(components) >= 2, (seed, difficulty, color, components)
            sizes = sorted((len(component) for component in components), reverse=True)
            assert sizes[0] > sizes[1], (seed, difficulty, color, sizes)
        largest2 = max(_components(grid, 2), key=len)
        largest3 = max(_components(grid, 3), key=len)
        assert _normalized(largest2) & _normalized(largest3)


def test_grid_and_distractor_overrides_are_effective(generator):
    grid = generator.generate(
        19,
        4,
        difficulty="medium",
        grid_h=12,
        grid_w=15,
        distractor_count=3,
        texture="dense",
    )
    assert (len(grid), len(grid[0])) == (12, 15)
    assert generator.self_check(grid) == []
    assert len(_components(grid, 2)) == 4
    assert len(_components(grid, 3)) == 4


def test_self_check_rejects_tied_largest_components(generator):
    grid = [[0] * 10 for _ in range(8)]
    for color, left in ((2, 0), (3, 6)):
        grid[1][left] = color
        grid[1][left + 1] = color
        grid[5][left] = color
        grid[5][left + 1] = color
    errors = generator.self_check(grid)
    assert any("unique largest color-2" in error for error in errors)
    assert any("unique largest color-3" in error for error in errors)


def _all_cells_shortcut_sets(grid, generator):
    largest2 = max(_components(grid, 2), key=len)
    largest3 = max(_components(grid, 3), key=len)
    intended = _normalized(largest2) & _normalized(largest3)
    all2 = {(row, col) for row, values in enumerate(grid)
            for col, value in enumerate(values) if value == 2}
    all3 = {(row, col) for row, values in enumerate(grid)
            for col, value in enumerate(values) if value == 3}
    shortcut = _normalized(all2) & _normalized(all3)
    return intended, shortcut


def test_declared_global_size_overrides_work_across_difficulty(generator):
    grid = generator.generate(
        7,
        0,
        difficulty="easy",
        grid_h=20,
        grid_w=20,
        distractor_count=1,
        texture="sparse",
    )
    assert (len(grid), len(grid[0])) == (20, 20)
    assert generator.self_check(grid) == []


def test_degenerate_size_overrides_are_used_and_irrelevant_controls_rejected(generator):
    grid = generator.generate(3, 0, texture="no_shapes", grid_h=12, grid_w=14)
    assert (len(grid), len(grid[0])) == (12, 14)
    with pytest.raises(ValueError, match="distractor_count.*degenerate"):
        generator.generate(3, 0, texture="no_shapes", distractor_count=2)


def test_normal_generation_refutes_all_cells_shortcut(generator):
    grid = generator.generate(5, 0)
    intended, shortcut = _all_cells_shortcut_sets(grid, generator)
    assert intended != shortcut


def test_distractor_axis_metadata_matches_actual_default_range(generator):
    assert generator.AXES["distractor_count"]["default"] == "rng 1..3"


def test_no_intersection_degenerate_has_no_normalized_overlap(generator):
    grid = generator.generate(11, 0, texture="no_intersection")
    twos = {(row, col) for row, values in enumerate(grid)
            for col, value in enumerate(values) if value == 2}
    threes = {(row, col) for row, values in enumerate(grid)
              for col, value in enumerate(values) if value == 3}
    assert _normalized(twos).isdisjoint(_normalized(threes))
    assert generator.self_check(grid, meta={"texture": "no_intersection"}) == []
