"""Feasible partial controls must constrain the remaining dimension draws."""
from __future__ import annotations

import importlib
import importlib.util
from collections import Counter
from pathlib import Path
import sys

import pytest


TASK_ID = "11c53dabb028"


def _load_generator():
    try:
        from reviewer_support import find_root
    except ModuleNotFoundError as exc:
        if exc.name != "reviewer_support":
            raise
        for ancestor in Path(__file__).resolve().parents:
            runtime = ancestor / "shared" / "runtime"
            if (runtime / "reviewer_support.py").is_file():
                sys.path.insert(0, str(runtime))
                break
        else:
            raise
        from reviewer_support import find_root
    root = find_root(__file__)
    module_name = f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name not in {
            "puzzle_generators.per_puzzle",
            f"puzzle_generators.per_puzzle.{TASK_ID}",
            module_name,
        }:
            raise
        source = root / "generators" / TASK_ID / "generator.py"
        spec = importlib.util.spec_from_file_location("partial_override_generator", source)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


GEN = _load_generator()


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("axis", ["grid_h", "grid_w"])
def test_one_cell_dimension_with_multicolor_samples_a_feasible_other_dimension(difficulty, axis):
    # Seed 8 with grid_h=1 previously sampled an impossible width of 2.
    for seed in (0, 8, 19):
        grid = GEN.generate(seed, 0, difficulty=difficulty, **{
            axis: 1, "multi_color": True, "fg_color": 7,
        })
        height, width = len(grid), len(grid[0])
        assert (height if axis == "grid_h" else width) == 1
        assert height * width >= 3
        assert GEN.self_check(grid) == []
        nonzero = [value for row in grid for value in row if value]
        assert nonzero[0] == 7
        assert len(set(nonzero)) >= 2


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("extra_shape", [{}, {"grid_h": 10}, {"grid_w": 10}])
def test_sparse_density_with_multicolor_samples_feasible_dimensions(difficulty, extra_shape):
    # The requested density is realizable: area 150 rounds to two occupied
    # cells. Random small dimensions must not turn this into a rejection.
    grid = GEN.generate(0, 0, difficulty=difficulty, fg_density=0.01,
                        multi_color=True, fg_color=9, **extra_shape)
    height, width = len(grid), len(grid[0])
    area = height * width
    assert GEN.self_check(grid) == []
    for axis, value in extra_shape.items():
        assert (height if axis == "grid_h" else width) == value
    nonzero = [value for row in grid for value in row if value]
    assert len(nonzero) == min(area - 1, max(1, round(area * 0.01)))
    assert len(nonzero) >= 2
    assert nonzero[0] == 9
    assert len(set(nonzero)) >= 2


@pytest.mark.parametrize("options", [
    {"grid_h": 1, "grid_w": 1},
    {"grid_h": 1, "grid_w": 2, "multi_color": True},
    {"grid_h": 2, "grid_w": 1, "multi_color": True},
    {"fg_density": 0.0, "multi_color": True},
    {"grid_h": 9, "fg_density": 0.01, "multi_color": True},
    {"grid_w": 9, "fg_density": 0.01, "multi_color": True},
])
def test_impossible_partial_and_fully_pinned_controls_still_reject(options):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **options)


def _first_color(grid):
    return next(value for row in grid for value in row if value)


def _second_frequency_color(grid):
    colors = [value for row in grid for value in row if value]
    counts = Counter(colors)
    ordered = sorted(counts, key=lambda value: (-counts[value], colors.index(value)))
    return ordered[min(1, len(ordered) - 1)]


def _second_frequency_output(grid):
    height, width = len(grid), len(grid[0])
    color = _second_frequency_color(grid)
    return [[color if grid[r % height][c % width] == 0 else 0
             for c in range(2 * width)] for r in range(2 * height)]


def _mode_color(grid):
    counts = Counter(value for row in grid for value in row if value)
    return min(counts, key=lambda color: (-counts[color], color))


def test_second_frequency_is_a_declared_executable_canonical_shortcut():
    # Before the repair this frequency selector fits every default, although
    # it fails on a lawful input whose first color is the unique majority.
    counterexample = [[2, 2, 2], [8, 0, 9]]
    assert GEN.self_check(counterexample) == []
    assert _first_color(counterexample) == 2
    assert _second_frequency_color(counterexample) == 8
    for declaration in (GEN.CANONICAL_SHORTCUTS, GEN.LESSON_COMPETITORS, GEN.SEMANTIC_RIVALS):
        assert "second_frequency" in declaration
        for grid in (counterexample, [[0, 4], [4, 0]], [[0, 7, 2], [7, 2, 5]]):
            assert declaration["second_frequency"](grid) == _second_frequency_output(grid)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_frequency_roles_refute_mode_and_runner_up_under_every_query_rotation(difficulty):
    for start in range(6):
        grids = [GEN.generate(41, start + offset, difficulty=difficulty) for offset in range(6)]
        majority = 0
        minority = 0
        for grid in grids:
            colors = [value for row in grid for value in row if value]
            if len(set(colors)) > 1:
                first_count = colors.count(colors[0])
                majority += first_count > len(colors) / 2
                minority += first_count < max(Counter(colors).values())
        assert (majority, minority) == (2, 2)
        for query_index in range(6):
            demos = [grid for index, grid in enumerate(grids) if index != query_index]
            assert any(_second_frequency_color(grid) != _first_color(grid) for grid in demos)
            assert any(_mode_color(grid) != _first_color(grid) for grid in demos)
