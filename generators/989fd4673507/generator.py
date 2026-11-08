"""Generator for 9aec4887.

Rule: color-8 shape is framed by colors of its nearest uniquely
closest edge.

Combinatorial axes (8): grid_h/w, shape, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_distinct_colors.
Degenerates: no_shape, no_edges, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.shape import PLUS_5

GENERATOR_ID = "989fd4673507"
VERSION = "2.0.0"  # in_sh=1 / out_sh=2: fixed 12x13 grid + 3-shape bank + fixed edge box. Output dims = (8-bbox)+2 and the 8-shape alone drives the interior; the 4 markers only supply colors+orientation (box geometry is irrelevant to output). Vary grid size, box, and use a RANDOM 8-polyomino (varied non-square bbox) -> output dims and content vary.
TASK_ID = "989fd4673507"
SUMMARY = "Four colored edge markers (2 horizontal, 2 vertical) + one separate color-8 polyomino. The rule frames the 8-shape's bbox, coloring each interior 8-cell by its nearest edge (ties stay 8); output dims = (eh+2)x(ew+2). The 8-shape, the marker colors and the grid size all vary."

INVARIANTS = [
    "four non-8 colors form two horizontal and two vertical guide edges",
    "one separate color-8 shape defines the output interior mask",
    "edge colors are distinct from each other and from 0 and 8",
    "shape sits clear of the edges",
]

SHAPE_NAMES = ("plus", "zigzag", "block")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_shape", "no_edges", "full_grid")
HELPFUL_TEXTURES = SHAPE_NAMES

SHAPES = {
    "plus": PLUS_5,
    "zigzag": [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],
    "block": [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)],
}

AXES = {
    "grid_h":         {"type": "int", "default": "12", "valid": "12"},
    "grid_w":         {"type": "int", "default": "13", "valid": "13"},
    "shape":          {"type": "str", "default": "rng helpful",
                       "valid": "|".join(SHAPE_NAMES)},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "4", "valid": "4"},
    "texture":        {"type": "str", "default": "alias for shape",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _free(g, r0, c0, sh, sw):
    h, w = len(g), len(g[0])
    if r0 < 0 or c0 < 0 or r0 + sh > h or c0 + sw > w:
        return False
    for r in range(max(0, r0 - 1), min(h, r0 + sh + 1)):
        for c in range(max(0, c0 - 1), min(w, c0 + sw + 1)):
            if g[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 13); w = ctx.draw_int("grid_w", 12, 14)
        s_lo, s_hi = 5, 8
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 15, 19); w = ctx.draw_int("grid_w", 16, 20)
        s_lo, s_hi = 9, 16
    else:
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 13, 17)
        s_lo, s_hi = 6, 12
    top, bottom, left, right = ctx.draw_distinct_colors("edge_colors", n=4, exclude={0, 8})
    # The box geometry doesn't affect the output (the rule reads only the
    # markers' colors + orientation/ordering), but a rectangular box keeps the
    # input on-distribution. The 8-polyomino drives the output entirely.
    for _ in range(60):
        g = full_grid(h, w, 0)
        bh = rng.randint(4, 6); bw = rng.randint(4, 6)
        br = rng.randint(0, h - bh); bc = rng.randint(0, w - bw)
        for c in range(bc, bc + bw):
            g[br][c] = top; g[br + bh - 1][c] = bottom
        for r in range(br + 1, br + bh - 1):
            g[r][bc] = left; g[r][bc + bw - 1] = right
        # random 8-shape (bbox >= 2x2 so output >= 4x4), placed clear of the box
        for _try in range(40):
            shape = _rand_poly(rng, rng.randint(s_lo, s_hi))
            sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
            if sh < 2 or sw < 2 or sh > h - 2 or sw > w - 2:
                continue
            r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
            if _free(g, r0, c0, sh, sw):
                paint_at(g, r0, c0, shape, 8)
                return g
    raise ValueError("could not place box + 8-shape")


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 13, 0)
    if name == "no_shape":
        for c in range(3, 10):
            g[1][c] = 1; g[8][c] = 2
        return g
    if name == "no_edges":
        paint_at(g, 4, 5, PLUS_5, 8)
        return g
    if name == "full_grid":
        for r in range(12):
            for c in range(13):
                g[r][c] = 8
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid is empty or ragged"]
    h, w = len(grid), len(grid[0])
    eight = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if not eight:
        errs.append("no color-8 shape")
    edge_colors = sorted({v for row in grid for v in row if v not in (0, 8)})
    if len(edge_colors) != 4:
        errs.append(f"expected four distinct edge colors, found {len(edge_colors)}")
    for color in edge_colors:
        cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
        rows = {r for r, _ in cells}; cols = {c for _, c in cells}
        if len(rows) != 1 and len(cols) != 1:
            errs.append(f"edge color {color} is not a straight horizontal/vertical guide")
            break
    return errs
