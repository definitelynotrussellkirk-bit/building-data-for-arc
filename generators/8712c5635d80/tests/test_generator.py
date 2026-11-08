from __future__ import annotations

import copy
import importlib
import json
import random

import pytest

from reviewer_support import canonical_pairs, find_root


gen = importlib.import_module("puzzle_generators.per_puzzle.8712c5635d80.generator")
ROOT = find_root(__file__)
TASK_ID = "8712c5635d80"


def _separator(grid):
    cols = [
        c
        for c in range(len(grid[0]))
        if all(grid[r][c] == 9 for r in range(len(grid)))
    ]
    assert len(cols) == 1
    return cols[0]


def _frame_facts(grid):
    sep = _separator(grid)
    h = len(grid)
    panel = sep
    right0 = sep + 1
    perimeter = {
        (r, c)
        for r in range(h)
        for c in range(right0, len(grid[0]))
        if r in (0, h - 1) or c in (right0, len(grid[0]) - 1)
    }
    interior = {
        (r, c)
        for r in range(1, h - 1)
        for c in range(right0 + 1, len(grid[0]) - 1)
    }
    frame_colors = {grid[r][c] for r, c in perimeter}
    return sep, panel, perimeter, interior, frame_colors


def _expected_output(grid):
    sep = _separator(grid)
    frame_color = next(
        grid[r][c]
        for r in range(len(grid))
        for c in range(sep + 1, len(grid[0]))
        if grid[r][c] != 0
    )
    out = copy.deepcopy(grid)
    for r in range(len(grid)):
        for c in range(sep):
            if grid[r][c] != 0:
                out[r][sep + 1 + c] = frame_color
    return out


def test_canonical_inputs_are_owned_by_the_generator():
    assert gen.RULE_HASH == "2c2e07bc5619"
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert _expected_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_inputs_have_a_full_perimeter_frame(band):
    for index in range(24):
        grid = gen.generate(1000 + index, index * 11, difficulty=band)
        sep, panel, perimeter, interior, frame_colors = _frame_facts(grid)
        assert len(grid) == panel
        assert len(grid[0]) == 2 * panel + 1
        assert len(frame_colors) == 1
        frame_color = next(iter(frame_colors))
        assert frame_color in range(1, 9)
        assert all(grid[r][c] == frame_color for r, c in perimeter)
        assert all(grid[r][c] == 0 for r, c in interior)
        left = [(r, c, grid[r][c]) for r in range(len(grid)) for c in range(sep) if grid[r][c]]
        assert 3 <= len(left) <= 9
        assert all(0 < r < len(grid) - 1 and 0 < c < sep - 1 for r, c, _ in left)
        assert len({value for _, _, value in left}) == 1
        assert left[0][2] != frame_color
        assert gen.self_check(grid) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"panel_size": 5, "shape_size": 3, "palette_id": 0},
        {"panel_size": 6, "shape_size": 5, "palette_id": 17},
        {"panel_size": 14, "shape_size": 9, "palette_id": 55},
    ],
)
def test_exact_overrides_are_observable_in_every_band(band, options):
    grid = gen.generate(19, 7, difficulty=band, **options)
    assert gen.observe_overrides(grid) == options
    assert gen.self_check(grid) == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown": 1},
        {"panel_size": 4},
        {"panel_size": 15},
        {"shape_size": 2},
        {"shape_size": 10},
        {"palette_id": -1},
        {"palette_id": 56},
        {"panel_size": True},
        {"shape_size": 4.5},
        {"palette_id": "3"},
    ],
)
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


def test_single_marker_regression_is_rejected_and_refuted():
    counterexample_path = (
        ROOT
        / "generators"
        / TASK_ID
        / "counterexamples"
        / "single_marker_shortcut.json"
    )
    counterexample = json.loads(counterexample_path.read_text())
    grid = counterexample["input"]

    assert gen.self_check(grid) == []
    assert gen.SEMANTIC_WITNESSES["full_frame_context"](grid)
    assert _expected_output(grid) == counterexample["expected_output"]

    rival = gen.SEMANTIC_RIVALS["single_marker_only"](grid)
    assert rival == counterexample["rival_output"]
    assert rival != counterexample["expected_output"]
    assert rival == gen.CANONICAL_SHORTCUTS["single_marker_only"](grid)

    marker_only_input = copy.deepcopy(grid)
    sep, _, perimeter, _, _ = _frame_facts(marker_only_input)
    keep = min(perimeter)
    for r, c in perimeter:
        if (r, c) != keep:
            marker_only_input[r][c] = 0
    assert gen.self_check(marker_only_input)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(8128)
    state = random.getstate()
    first = gen.generate(71, 4, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(71, 4, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 0
    assert gen.generate(71, 4, difficulty="hard") == second
