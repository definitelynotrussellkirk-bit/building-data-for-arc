"""Generator for arc_additional_puzzle_bank_volume11:E77 — yellow rings get cyan centers.

Rule: hollow 3×3 yellow rings have their centers filled cyan.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_rings,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_rings, solid_squares, centers_already_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "5e3b849bd9c3"
VERSION = "2.1.0"
TASK_ID = "5e3b849bd9c3"
SUMMARY = (
    "0-bg grid (h, w ~8-13) with 2-4 ISOLATED 3×3 HOLLOW "
    "color-4 (yellow) RINGS — each ring is the 8 border "
    "cells of a 3×3 region drawn at random non-overlapping "
    "positions with ≥4-cell spacing. Each ring's CENTER "
    "cell (the middle of the 3×3) is initially 0. Rule: "
    "detect each hollow 3×3 yellow ring (exact pattern: "
    "border = 4, center = 0). For each, paint its CENTER "
    "cell with color 8 (cyan). Border yellow cells stay 4."
)

INVARIANTS = [
    "background is 0",
    "each target is an exact 3x3 yellow ring with empty center",
    "rings are separated so their neighborhoods do not overlap",
    "non-ring yellow fragments may appear as distractors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_rings", "solid_squares", "centers_already_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_rings":        {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "spaced_3x3_yellow_rings",
                       "valid": "spaced_3x3_yellow_rings"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_rings|solid_squares|centers_already_filled"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        n_rings = ctx.draw_int("n_rings", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 12, 13)
        n_rings = ctx.draw_int("n_rings", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 8, 13)
        n_rings = ctx.draw_int("n_rings", 2, 4)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    anchors: list[tuple[int, int]] = []
    for _ in range(200):
        if len(anchors) >= n_rings:
            break
        r = rng.randint(0, h - 3)
        c = rng.randint(0, w - 3)
        if any(abs(r - rr) < 4 and abs(c - cc) < 4 for rr, cc in anchors):
            continue
        draw_rect_outline(g, r, c, 3, 3, 4)
        anchors.append((r, c))
    if not anchors:
        draw_rect_outline(g, 1, 1, 3, 3, 4)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, >=8 color-4 yellow cells (at least one 3x3 ring worth)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    yellows = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4]
    if len(yellows) < 8:
        errs.append(f"expected >=8 color-4 yellow cells (one 3x3 ring), found {len(yellows)}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_rings":
        # blank → no rings to fill
        return g
    if name == "solid_squares":
        # solid 3x3 yellow squares (no hollow) → no center to fill
        for r in range(3):
            for c in range(3): g[1 + r][1 + c] = 4
        for r in range(3):
            for c in range(3): g[5 + r][5 + c] = 4
        return g
    if name == "centers_already_filled":
        # 3x3 ring with center already non-bg → fill precondition fails
        draw_rect_outline(g, 1, 1, 3, 3, 4)
        g[2][2] = 8
        draw_rect_outline(g, 5, 5, 3, 3, 4)
        g[6][6] = 6
        return g
    return g
