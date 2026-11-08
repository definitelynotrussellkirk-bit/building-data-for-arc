"""Source-review regressions for d1c500f060a1."""
from __future__ import annotations

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "d1c500f060a1"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)


def _codes(grid):
    return tuple(value for value in grid[0] if value)


def _motif_signature(grid):
    cells = [(r, c) for r, row in enumerate(grid[2:], start=2)
             for c, value in enumerate(row) if value]
    r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _motif_colors(grid):
    return tuple(sorted({value for row in grid[2:] for value in row if value}))


def test_all_original_pairs_are_valid_and_mirrored_exactly():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_ordinary_generation_uses_only_defined_codes_and_varied_motifs():
    grids = [GEN.generate(818, index, difficulty="medium") for index in range(40)]
    assert all(GEN.self_check(grid, difficulty="medium") == [] for grid in grids)
    assert all(set(_codes(grid)) <= set(range(1, 6)) for grid in grids)
    assert all(all(value == 0 for value in grid[1]) for grid in grids)
    assert len({_motif_signature(grid) for grid in grids}) >= 5
    assert set().union(*map(set, map(_codes, grids))) == set(range(1, 6))


def test_palette_and_texture_controls_change_visible_motif():
    common = dict(grid_h=14, grid_w=16, n_codes=4, texture="hook5")
    warm = GEN.generate(23, 1, palette_kind="warm", **common)
    cool = GEN.generate(23, 1, palette_kind="cool", **common)
    fork = GEN.generate(23, 1, palette_kind="warm", grid_h=14, grid_w=16,
                        n_codes=4, texture="fork7")
    assert _motif_colors(warm) != _motif_colors(cool)
    assert _motif_signature(warm) != _motif_signature(fork)


def test_self_check_rejects_two_color_motif_without_singleton_accent():
    grid = GEN.generate(23, 1, grid_h=14, grid_w=16, n_codes=4,
                        palette_kind="warm", texture="hook5")
    cells = [(r, c) for r, row in enumerate(grid[2:], start=2)
             for c, value in enumerate(row) if value]
    counts = {}
    for r, c in cells:
        counts[grid[r][c]] = counts.get(grid[r][c], 0) + 1
    accent = next(color for color, count in counts.items() if count == 1)
    body_cell = next((r, c) for r, c in cells if grid[r][c] != accent)
    grid[body_cell[0]][body_cell[1]] = accent
    assert GEN.self_check(grid) == ["motif must have exactly one singleton accent"]


def test_exact_30_by_30_case_stays_within_arc_output_bounds():
    grid = GEN.generate(9, 3, difficulty="hard", grid_h=30, grid_w=30,
                        n_codes=5, palette_kind="varied", texture="block_notch8")
    assert (len(grid), len(grid[0])) == (30, 30)
    assert GEN.self_check(grid) == []
    output = GEN.rule_mirror(grid)
    assert 1 <= len(output) <= 30 and 1 <= len(output[0]) <= 30
    assert sum(value != 0 for row in output for value in row) >= 35


@pytest.mark.parametrize("kwargs", [
    {"seed": True}, {"seed": 1.0}, {"sample_index": -1},
    {"sample_index": False}, {"difficulty": "impossible"},
    {"mystery_axis": 1}, {"grid_h": 5}, {"n_codes": 6},
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
