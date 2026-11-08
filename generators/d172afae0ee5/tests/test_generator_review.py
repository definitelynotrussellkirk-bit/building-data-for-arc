"""Source-review regressions for d172afae0ee5."""
from __future__ import annotations

from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "d172afae0ee5"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)


def _object_signature(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
             if value not in (0, 9)]
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _object_color(grid):
    return next(value for row in grid for value in row if value not in (0, 9))


def test_all_original_pairs_are_valid_and_mirrored_exactly():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_ordinary_generation_covers_multiple_canonical_shape_profiles():
    grids = [GEN.generate(731, index, difficulty="medium") for index in range(36)]
    assert all(GEN.self_check(grid, difficulty="medium") == [] for grid in grids)
    signatures = {_object_signature(grid) for grid in grids}
    canonical = {_object_signature(pair["input"])
                 for pair in canonical_pairs(TASK, root=ROOT, labeled_only=True)}
    assert len(signatures) >= 5
    assert len(signatures & canonical) >= 4


def test_palette_and_texture_controls_change_visible_content():
    common = dict(grid_h=14, grid_w=15, texture="canonical_l4")
    warm = GEN.generate(19, 2, palette_kind="warm", **common)
    cool = GEN.generate(19, 2, palette_kind="cool", **common)
    zig = GEN.generate(19, 2, palette_kind="warm", grid_h=14, grid_w=15,
                       texture="canonical_zig4")
    assert _object_color(warm) != _object_color(cool)
    assert _object_signature(warm) != _object_signature(zig)


def test_exact_controls_support_a_valid_30_by_30_scene():
    grid = GEN.generate(101, 4, difficulty="hard", grid_h=30, grid_w=30,
                        palette_kind="varied", texture="stair8")
    assert (len(grid), len(grid[0])) == (30, 30)
    assert GEN.self_check(grid, difficulty="hard") == []
    output = GEN.rule_mirror(grid)
    marker = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                  if value == 9)
    out_cells = [(r, c) for r, row in enumerate(output) for c, value in enumerate(row)
                 if value != 0]
    assert marker == (min(r for r, _ in out_cells), min(c for _, c in out_cells))
    assert len(out_cells) >= 8


@pytest.mark.parametrize("kwargs", [
    {"seed": True}, {"seed": 1.0}, {"sample_index": -1},
    {"sample_index": False}, {"difficulty": "impossible"},
    {"mystery_axis": 1}, {"grid_h": 5}, {"object_color": 9},
    {"palette_kind": "neon"}, {"texture": "unknown"},
])
def test_invalid_calls_are_rejected(kwargs):
    call = dict(seed=1, sample_index=0, difficulty=None)
    call.update(kwargs)
    seed = call.pop("seed")
    sample_index = call.pop("sample_index")
    difficulty = call.pop("difficulty")
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, sample_index, difficulty=difficulty, **call)
