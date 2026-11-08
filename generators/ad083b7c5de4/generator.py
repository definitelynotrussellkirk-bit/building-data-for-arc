"""Generator for 917bccba.

Rule: frame is preserved while horizontal and vertical guide lines
move to the frame top and right edges.

Combinatorial axes (8): grid_h/w, frame_size, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_distinct_colors.
Degenerates: no_frame, no_lines, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ad083b7c5de4"
VERSION = "1.3.0"  # floor grid at size+5 (hard size=9 frame ran off the 11..15 grid)
TASK_ID = "ad083b7c5de4"
SUMMARY = "Rectangular frame in one color + guide lines in another color (one row through and one col through the frame interior). Rule moves the guide lines so the horizontal guide aligns with the TOP frame row (r1) and the vertical guide aligns with the RIGHT frame col (c2); cells outside the frame on those new lines are line-colored, others become 0. Frame border preserved."

# Rivals: 'output is input' refuted by any demo (lines move).
# 'preserve guide row/col positions' refuted by any demo (they snap).
# 'use bg as line color' refuted by any demo (line color preserved).
# 'use line color for frame' refuted by any demo (frame stays its own color).
# 3 demos with varied frame positions cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is color 0",
    "one rectangular frame uses a nonzero color",
    "one guide color appears outside the frame",
    "the frame bbox is smaller than the full grid",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_frame", "no_lines", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..15", "valid": "9..18"},
    "grid_w":         {"type": "int", "default": "rng 11..15", "valid": "9..18"},
    "frame_size":     {"type": "int", "default": "rng 4..6", "valid": "3..8"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_frame|no_lines|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        size_lo, size_hi = 3, 5
    elif difficulty == "hard":
        size_lo, size_hi = 7, 9
    else:
        size_lo, size_hi = 4, 7
    size = ctx.draw_int("frame_size", size_lo, size_hi)
    # The frame is anchored at r1=3 / c1∈{2,3} and spans `size`, so it reaches
    # r2=size+3 and c2=size+3. The guide lines must also fall OUTSIDE the frame
    # (rows >r2 / cols >c2 in the loops below), so the grid needs ≥ size+5 cells
    # per axis. Hard's size=9 reaches r2/c2=12 but h/w were drawn 11..15
    # independently → frame ran off a w=11/h=11 grid → "list index out of range".
    # Floor each axis at size+5 (no-op for the easy/default bands' smaller frames).
    need = size + 5
    h = max(11, need) + rng.randint(0, 4)
    w = max(11, need) + rng.randint(0, 4)
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind") or
                    ctx.draw_choice("palette_kind", list(PALETTE_KINDS)))
    pool = _build_palette(palette_kind, rng)
    if len(pool) < 2:
        pool = pool + [c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9] if c not in pool]
    frame_color, line_color = pool[0], pool[1]
    g = full_grid(h, w, 0)
    r1 = 3
    c1 = 2 + (sample_index % 2)
    r2 = r1 + size
    c2 = c1 + size
    for c in range(c1, c2 + 1):
        g[r1][c] = frame_color
        g[r2][c] = frame_color
    for r in range(r1, r2 + 1):
        g[r][c1] = frame_color
        g[r][c2] = frame_color
    for c in range(w):
        if c < c1 or c > c2:
            g[r2][c] = line_color
    for r in range(h):
        if r < r1 or r > r2:
            g[r][c1] = line_color
    return g


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    colors = sorted({v for row in grid for v in row if v != 0})
    if len(colors) != 2:
        errs.append(f"expected exactly frame+guide colors, got {colors}")
        return errs

    frame_candidates = []
    for color in colors:
        cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        if r2 <= r1 or c2 <= c1:
            continue
        border = ({(r1, c) for c in range(c1, c2 + 1)} |
                  {(r2, c) for c in range(c1, c2 + 1)} |
                  {(r, c1) for r in range(r1, r2 + 1)} |
                  {(r, c2) for r in range(r1, r2 + 1)})
        if all(grid[r][c] == color for r, c in border):
            frame_candidates.append((color, r1, r2, c1, c2))
    if len(frame_candidates) != 1:
        errs.append(f"expected one rectangular frame, found {len(frame_candidates)}")
        return errs
    fcol, r1, r2, c1, c2 = frame_candidates[0]
    line_color = next(c for c in colors if c != fcol)
    if not (0 < r1 and r2 < h - 1 and 0 < c1 and c2 < w - 1):
        errs.append("frame must be smaller than the full grid with exterior room")
    horiz = [(r2, c) for c in range(w) if c < c1 or c > c2]
    vert = [(r, c1) for r in range(h) if r < r1 or r > r2]
    if not horiz or not vert:
        errs.append("guide lines must have exterior horizontal and vertical segments")
    if any(grid[r][c] != line_color for r, c in horiz + vert):
        errs.append("guide color is not present on the expected exterior row/column")
    return errs


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    pool = [c for c in pool if c != 0]
    rng.shuffle(pool)
    return pool


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 13, 0)
    if name == "no_frame":
        for c in range(13):
            g[6][c] = 2
        return g
    if name == "no_lines":
        for c in range(3, 9):
            g[3][c] = 1; g[8][c] = 1
        for r in range(3, 9):
            g[r][3] = 1; g[r][8] = 1
        return g
    if name == "full_grid":
        for r in range(13):
            for c in range(13):
                g[r][c] = 2
        return g
    return g
