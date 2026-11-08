from __future__ import annotations

import importlib
import json
import random
from pathlib import Path

import pytest


TASK = "a85b9271a0ee"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def independent_shift(grid):
    height, width = len(grid), len(grid[0])
    out = [[0] * width for _ in range(height)]
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value != 0 and row + 1 < height and col + 1 < width:
                out[row + 1][col + 1] = value
    return out


def canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row
    raise AssertionError("canonical task missing")


def canonical_pairs():
    row = canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return row["train"] + test


def test_canonical_rule_statement_and_hash_pin_match_every_pair():
    assert MODULE.RULE_HASH == "966b5b4d8247"
    for pair in canonical_pairs():
        assert independent_shift(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_generated_scenes_are_lawful_and_exercise_both_edge_branches(difficulty):
    modes = set()
    for seed in range(120):
        grid = MODULE.generate(seed, seed * 13 + 5, difficulty=difficulty)
        observed = MODULE.observe_overrides(grid)
        assert MODULE.self_check(grid, difficulty=difficulty) == []
        assert independent_shift(grid) != grid
        assert sum(value != 0 for row in independent_shift(grid) for value in row) >= 1
        modes.add(observed["edge_mode"])
    assert modes == set(MODULE.EDGE_MODES)


@pytest.mark.parametrize(
    "case",
    [
        {"grid_h": 6},
        {"grid_h": 12},
        {"grid_w": 6},
        {"grid_w": 12},
        {"n_cells": 3},
        {"n_cells": 12},
        {"n_components": 1},
        {"n_components": 3},
        {"edge_mode": "in_bounds"},
        {"edge_mode": "mixed"},
        {
            "grid_h": 6,
            "grid_w": 6,
            "n_cells": 12,
            "n_components": 3,
            "edge_mode": "mixed",
        },
        {
            "grid_h": 12,
            "grid_w": 12,
            "n_cells": 3,
            "n_components": 1,
            "edge_mode": "in_bounds",
        },
    ],
)
@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exact_boundary_overrides_are_observable(case, difficulty):
    grid = MODULE.generate(9107, 37, difficulty=difficulty, **case)
    observed = MODULE.observe_overrides(grid)
    for axis, expected in case.items():
        assert observed[axis] == expected
    assert MODULE.self_check(
        grid, difficulty=difficulty, meta={"overrides": case}
    ) == []


def test_incompatible_and_unknown_controls_fail_loudly():
    with pytest.raises(ValueError, match="cannot realize"):
        MODULE.generate(1, 0, n_cells=3, n_components=3)
    with pytest.raises(ValueError, match="unknown override"):
        MODULE.generate(1, 0, texture="empty_grid")
    with pytest.raises(ValueError, match="difficulty"):
        MODULE.generate(1, 0, difficulty="expert")


def test_self_check_rejects_targeted_rule_hiding_impostors():
    height = width = 6
    impostors = {
        "all_background": [[0] * width for _ in range(height)],
        "singleton": [[0] * width for _ in range(height)],
        "short_line": [[0] * width for _ in range(height)],
        "solid_2x2": [[0] * width for _ in range(height)],
        "all_clipped": [[0] * width for _ in range(height)],
    }
    impostors["singleton"][2][2] = 4
    for col in range(1, 5):
        impostors["short_line"][2][col] = 4
    for row in range(2):
        for col in range(2):
            impostors["solid_2x2"][row + 2][col + 2] = 4
    for row, col in ((5, 1), (5, 2), (5, 3)):
        impostors["all_clipped"][row][col] = 4

    for name, grid in impostors.items():
        assert MODULE.self_check(grid), name


def test_component_palette_contract_rejects_recombined_scenes():
    grid = MODULE.generate(
        4801,
        11,
        difficulty="hard",
        n_cells=12,
        n_components=3,
        edge_mode="mixed",
    )
    components = MODULE._components(MODULE._foreground(grid))

    shared_color = [row[:] for row in grid]
    first_color = shared_color[next(iter(components[0]))[0]][next(iter(components[0]))[1]]
    for row, col in components[1]:
        shared_color[row][col] = first_color
    assert MODULE.self_check(shared_color)

    multicolor_component = [row[:] for row in grid]
    row, col = min(components[0])
    multicolor_component[row][col] = next(
        color for color in range(1, 10) if color != multicolor_component[row][col]
    )
    assert MODULE.self_check(multicolor_component)


def test_determinism_fresh_returns_and_global_rng_independence():
    random.seed(0xA85B)
    state = random.getstate()
    first = MODULE.generate(73, 6, difficulty="medium", edge_mode="mixed")
    assert random.getstate() == state
    second = MODULE.generate(73, 6, difficulty="medium", edge_mode="mixed")
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert MODULE.generate(73, 6, difficulty="medium", edge_mode="mixed") == second


def test_large_sample_has_shape_component_palette_and_output_diversity():
    grids = [MODULE.generate(seed, seed + 3) for seed in range(300)]
    outputs = [independent_shift(grid) for grid in grids]
    observed = [MODULE.observe_overrides(grid) for grid in grids]
    assert len({frozen(grid) for grid in grids}) >= 285
    assert len({frozen(grid) for grid in outputs}) >= 280
    assert len({(len(grid), len(grid[0])) for grid in grids}) >= 30
    assert {row["n_components"] for row in observed} == {1, 2, 3}
    assert {row["edge_mode"] for row in observed} == set(MODULE.EDGE_MODES)


def test_axis_contract_is_literal_and_minimal():
    assert set(MODULE.AXES) == {
        "grid_h",
        "grid_w",
        "n_cells",
        "n_components",
        "edge_mode",
    }
    assert tuple(MODULE.AXES["edge_mode"]["valid"].split("|")) == MODULE.EDGE_MODES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()
