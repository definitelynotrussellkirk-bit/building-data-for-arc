"""Source-review regressions for 329f699c3e09."""
from __future__ import annotations

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "329f699c3e09"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)


def _divider(grid):
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(h) if all(grid[r][c] == 7 for c in range(w))]
    cols = [c for c in range(w) if all(grid[r][c] == 7 for r in range(h))]
    assert len(rows) + len(cols) == 1
    return ("row", rows[0]) if rows else ("col", cols[0])


def _destinations(grid):
    axis, div = _divider(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 6:
                yield (2 * div - r, c) if axis == "row" else (r, 2 * div - c)


def test_all_original_labels_match_python_mirror():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "medium", "easy", "hard"])
def test_ordinary_generation_reserves_every_reflection_destination(difficulty):
    for index in range(80):
        grid = GEN.generate(7301, index, difficulty=difficulty)
        assert GEN.self_check(grid, difficulty=difficulty) == []
        for r, c in _destinations(grid):
            assert grid[r][c] == 0


def test_self_check_rejects_occupied_reflection_destination():
    grid = GEN.generate(26, 26, difficulty="easy")
    r, c = next(iter(_destinations(grid)))
    grid[r][c] = 4
    errors = GEN.self_check(grid, difficulty="easy")
    assert any("reflection destination" in error for error in errors)


def test_exact_controls_support_substantive_30_by_30_scene():
    grid = GEN.generate(
        101, 4, difficulty="hard", grid_h=30, grid_w=30,
        n_cells=18, palette_kind="varied",
    )
    assert (len(grid), len(grid[0])) == (30, 30)
    assert GEN.self_check(grid, difficulty="hard") == []
    output = GEN.rule_mirror(grid)
    assert sum(value == 6 for row in grid for value in row) >= 18
    assert sum(value == 8 for row in output for value in row) >= 18
    assert any(value not in (0, 6, 7) for row in grid for value in row)


@pytest.mark.parametrize("kwargs", [
    {"seed": True}, {"sample_index": -1}, {"difficulty": "impossible"},
    {"mystery": 1}, {"grid_h": 4}, {"grid_w": 31},
    {"n_cells": 0}, {"palette_kind": "neon"},
])
def test_invalid_requests_are_rejected(kwargs):
    call = dict(seed=1, sample_index=0, difficulty=None)
    call.update(kwargs)
    seed = call.pop("seed")
    sample_index = call.pop("sample_index")
    difficulty = call.pop("difficulty")
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, sample_index, difficulty=difficulty, **call)
