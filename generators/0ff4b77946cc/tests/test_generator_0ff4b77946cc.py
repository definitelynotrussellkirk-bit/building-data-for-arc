"""Focused regressions for non-lossy sorted-gallery generation."""
from __future__ import annotations

from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
GEN, _SOURCE, _SHA = load_selected_generator("0ff4b77946cc", root=ROOT)

AUDIT_INPUT = [
    [0,0,0,0,0,0,0,0,0,0,0],
    [0,5,5,5,0,0,0,0,0,0,0],
    [0,0,5,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0],
    [8,8,8,0,0,0,0,0,0,0,0],
    [8,8,8,0,0,0,0,0,0,0,0],
    [8,8,8,0,0,0,0,0,1,1,0],
    [0,0,0,0,0,6,0,0,0,1,0],
]


def _packed_width(grid):
    comps = GEN._components_by_color(grid)
    widths = []
    for _color, cells in comps:
        cols = [c for _r, c in cells]
        widths.append(max(cols) - min(cols) + 1)
    return sum(widths) + max(0, len(widths) - 1)


def test_retained_lossy_counterexample_is_rejected():
    errors = GEN.self_check(AUDIT_INPUT, difficulty="easy")
    assert any("packed width" in error for error in errors)


def test_normal_generation_never_exceeds_output_canvas():
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in (0, 1, 17, 20261025):
            for index in range(80):
                grid = GEN.generate(seed, index, difficulty=difficulty)
                assert GEN.self_check(grid, difficulty=difficulty) == []
                assert _packed_width(grid) <= len(grid[0])
                assert GEN.generate(seed, index, difficulty=difficulty) == grid


def test_degenerate_controls_remain_available():
    for texture in GEN.DEGENERATE_TEXTURES:
        grid = GEN.generate(0, 0, texture=texture)
        # Degenerate controls are intentionally outside the ordinary invariant.
        assert grid and grid[0]
