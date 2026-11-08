"""Source-review regressions for 2f4a0e633093."""
from __future__ import annotations

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "2f4a0e633093"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)


def _legend(grid):
    return [value for value in grid[0] if value]


def _panel_counts(grid):
    return [sum(grid[r][c] != 0 for r in range(2, 5) for c in range(c0, c0 + 3))
            for c0 in (0, 4, 8)]


def test_all_original_labels_match_python_mirror():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "medium", "easy", "hard"])
def test_ordinary_generation_satisfies_exact_gallery_grammar(difficulty):
    for index in range(40):
        grid = GEN.generate(811, index, difficulty=difficulty)
        assert GEN.self_check(grid, difficulty=difficulty) == []
        assert len(_legend(grid)) == len(set(_legend(grid))) == 3
        assert all(3 <= count <= 6 for count in _panel_counts(grid))
        assert GEN.rule_mirror(grid)


def test_palette_and_panel_count_controls_are_live():
    sparse = GEN.generate(19, 2, palette_kind="warm", n_panel_cells=3)
    dense = GEN.generate(19, 2, palette_kind="cool", n_panel_cells=6)
    assert _panel_counts(sparse) == [3, 3, 3]
    assert _panel_counts(dense) == [6, 6, 6]
    assert set(_legend(sparse)) != set(_legend(dense))


def test_self_check_rejects_duplicate_legend_and_empty_panel():
    grid = GEN.generate(7, 1)
    cols = [c for c, value in enumerate(grid[0]) if value]
    grid[0][cols[1]] = grid[0][cols[0]]
    for r in range(2, 5):
        for c in range(4, 7):
            grid[r][c] = 0
    errors = GEN.self_check(grid)
    assert any("legend" in error for error in errors)
    assert any("panel 1" in error for error in errors)


@pytest.mark.parametrize("kwargs", [
    {"seed": True}, {"sample_index": -1}, {"difficulty": "impossible"},
    {"mystery": 1}, {"n_panel_cells": 2}, {"n_panel_cells": 7},
    {"palette_kind": "neon"},
])
def test_invalid_requests_are_rejected(kwargs):
    call = dict(seed=1, sample_index=0, difficulty=None)
    call.update(kwargs)
    seed = call.pop("seed")
    sample_index = call.pop("sample_index")
    difficulty = call.pop("difficulty")
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, sample_index, difficulty=difficulty, **call)
