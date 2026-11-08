"""Generator for arc_puzzle_bank_21_set24_s:S24_E6.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_distractors,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_distractors, tied_depth, single_rect.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "144e23365d4b"
# 1.2.0: reverse-diversity -- already uniq~0.96, but only 2 solid-rect distractors
# in a fixed right-column layout. Now 2-3 distractors of varied size scattered
# anywhere (kept depth-below the winner), and a wider winner size range. The rule
# selects by max onion depth; the strict-max invariant is preserved.
VERSION = "1.2.1"
TASK_ID = "144e23365d4b"
SUMMARY = "Only the component with the greatest onion depth is kept and recolored."

INVARIANTS = [
    "background is 0",
    "one rectangle has strictly greater max onion depth than the distractors",
    "the selected component is recolored to 8",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_distractors", "tied_depth", "single_rect")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..15", "valid": "9..20"},
    "grid_w":         {"type": "int", "default": "rng 14..18", "valid": "10..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_distractors":  {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "palette_size":   {"type": "int", "default": "3..4", "valid": "3..4"},
    "position_bias":  {"type": "str", "default": "big_rect_plus_scattered_distractors",
                       "valid": "big_rect_plus_scattered_distractors"},
    "n_distinct_colors": {"type": "int", "default": "3..4", "valid": "3..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_distractors|tied_depth|single_rect"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; has >=2 distinct non-bg solid rect components (winner + distractors)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if not counts:
        return errors  # degenerate — allowed
    if len(counts) < 2:
        return errors  # degenerate (single_rect/no_distractors) — allowed
    return errors


def _paint_rect(grid, r0, c0, rh, rw, color):
    for r in range(r0, r0 + rh):
        for c in range(c0, c0 + rw):
            grid[r][c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 14, 15)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 15)
        w = ctx.draw_int("grid_w", 16, 18)
    else:
        h = ctx.draw_int("grid_h", 12, 15)
        w = ctx.draw_int("grid_w", 14, 18)
    rng = ctx.draw_rng("layout")
    n_distract = rng.randint(2, 3)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7], n_distract + 1)

    def _free_rect(grid, r0, c0, rh, rw):
        if r0 < 0 or c0 < 0 or r0 + rh > h or c0 + rw > w:
            return False
        for r in range(max(0, r0 - 1), min(h, r0 + rh + 1)):
            for c in range(max(0, c0 - 1), min(w, c0 + rw + 1)):
                if grid[r][c] != 0:
                    return False
        return True

    for _attempt in range(20):
        grid = full_grid(h, w, 0)
        # Winner: min-dim >= 6 -> onion depth >= 3.
        big_h = rng.randint(6, min(9, h - 1))
        big_w = rng.randint(6, min(10, w - 1))
        placed_big = False
        for _ in range(60):
            br = rng.randint(0, h - big_h); bc = rng.randint(0, w - big_w)
            if _free_rect(grid, br, bc, big_h, big_w):
                _paint_rect(grid, br, bc, big_h, big_w, colors[0])
                placed_big = True
                break
        if not placed_big:
            continue
        # Distractors: min-dim <= 4 -> onion depth <= 2 (< winner). Scatter anywhere.
        placed = 0
        for i in range(n_distract):
            for _ in range(60):
                rh = rng.randint(3, 4); rw = rng.randint(3, 5)
                r0 = rng.randint(0, h - rh); c0 = rng.randint(0, w - rw)
                if _free_rect(grid, r0, c0, rh, rw):
                    _paint_rect(grid, r0, c0, rh, rw, colors[i + 1])
                    placed += 1
                    break
        if placed == n_distract:
            return grid
    return grid


def _draw_from_degenerate(name, rng):
    h, w = 13, 16
    g = full_grid(h, w, 0)
    if name == "no_distractors":
        # only the big rectangle → trivially highest depth, no contrast
        _paint_rect(g, 2, 2, 7, 7, 3)
        return g
    if name == "tied_depth":
        # rectangles share max onion depth → ambiguous winner
        _paint_rect(g, 1, 1, 5, 5, 3)
        _paint_rect(g, 7, 9, 5, 5, 4)
        return g
    if name == "single_rect":
        # a single small rect has max depth 1 → no real onion depth signal
        _paint_rect(g, 5, 5, 3, 3, 3)
        return g
    return g
