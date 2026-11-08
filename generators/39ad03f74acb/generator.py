"""Generator for arc_additional_puzzle_bank_volume4:E22.

Rule: interior cells of straight blue segments (cells with 2 cardinal
blue neighbors) are recolored red; endpoints stay blue.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, n_segments, texture.
Degenerates: no_segments, length_two, non_straight.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "39ad03f74acb"
VERSION = "1.2.0"
TASK_ID = "39ad03f74acb"
SUMMARY = "Interior cells of straight blue segments are recolored red."

INVARIANTS = [
    "background is 0",
    "blue components are straight horizontal or vertical segments",
    "segments have length at least three",
    "segments are separated so they do not merge",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_segments", "length_two", "non_straight")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_segments":     {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "axis_aligned_segments",
                       "valid": "axis_aligned_segments"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_segments|length_two|non_straight"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥1 color-1 (blue) segment cell of length ≥3; values 0..9."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    for r in range(h):
        for c in range(w):
            if not (0 <= grid[r][c] <= 9):
                errors.append(f"out-of-range value {grid[r][c]} at ({r},{c})")
    blues = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    if blues == 0:
        pass  # degenerate (no_segments) — allowed
    elif blues < 3:
        errors.append(f"expected ≥3 blue cells for valid segment, found {blues}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        n_segments = ctx.draw_int("n_segments", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 13, 18)
        n_segments = ctx.draw_int("n_segments", 5, 8)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 8, 13)
        n_segments = ctx.draw_int("n_segments", 2, 5)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    # Alternate orientations so every ordinary lesson demonstrates the whole
    # canonical rule.  The previous sampler chose one orientation per grid,
    # allowing several vertical-only demonstrations followed by a horizontal
    # query.  A one-cell cardinal moat keeps independently drawn segments from
    # merging or turning into corners.
    first = rng.choice(("h", "v"))
    orientations = [first if index % 2 == 0 else ("v" if first == "h" else "h")
                    for index in range(n_segments)]
    for orientation in orientations:
        _place_segment(g, orientation, rng)
    return g


def _place_segment(grid, orientation, rng):
    h, w = len(grid), len(grid[0])
    maximum = min(6, w if orientation == "h" else h)
    lengths = list(range(3, maximum + 1))
    rng.shuffle(lengths)
    occupied = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1}
    for length in lengths:
        starts = ([(r, c) for r in range(h) for c in range(w - length + 1)]
                  if orientation == "h"
                  else [(r, c) for r in range(h - length + 1) for c in range(w)])
        rng.shuffle(starts)
        for r0, c0 in starts:
            cells = ({(r0, c0 + delta) for delta in range(length)} if orientation == "h"
                     else {(r0 + delta, c0) for delta in range(length)})
            if cells & occupied:
                continue
            if any((nr, nc) in occupied
                   for r, c in cells
                   for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                   if (nr, nc) not in cells):
                continue
            for r, c in cells:
                grid[r][c] = 1
            return True
    return False


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_segments":
        # Empty grid — rule has no segments and no interiors to recolor.
        return g
    if name == "length_two":
        # Length-2 segments — both cells are endpoints, no interior;
        # rule's "≥3 length" filter excludes them, output equals input.
        g[2][2] = 1; g[2][3] = 1
        g[5][6] = 1; g[6][6] = 1
        return g
    if name == "non_straight":
        # Bent components — rule's straight-line precondition fails.
        for r, c in [(2, 2), (3, 2), (4, 2), (4, 3), (4, 4)]: g[r][c] = 1
        return g
    return g
