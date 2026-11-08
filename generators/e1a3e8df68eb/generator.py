"""Generator for e3f79277.

Rule: small h x w grid (5..7) with bg=7 + 3-cell triangle at one
corner; output 16x16 with corner-aligned framed L + diagonal.

Combinatorial axes (8): grid_h/w, corner, color, palette_kind,
anchor_corner, asymmetry_force, palette_size, l_shape_variant.
Degenerates: no_corner, all_corners, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e1a3e8df68eb"
VERSION = "1.2.0"  # add executable corner-marker invariant
TASK_ID = "e1a3e8df68eb"
SUMMARY = "Small bg=7 grid with 3-cell triangle in one corner of one non-7 color."

INVARIANTS = [
    "bg = 7",
    "3 non-bg cells forming an L-shape in one corner",
    "all other cells are bg",
]

CORNERS = ("tl", "tr", "bl", "br")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_corner", "all_corners", "full_grid")
HELPFUL_TEXTURES = CORNERS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..9"},
    "grid_w":         {"type": "int", "default": "rng 5..7", "valid": "4..9"},
    "corner":         {"type": "str", "default": "rng helpful",
                       "valid": "|".join(CORNERS)},
    "color":          {"type": "color", "default": "rng !7",
                       "valid": "1..6|8|9"},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "true",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for corner",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 4, 5
    elif difficulty == "hard":
        h_lo, h_hi = 7, 9
    else:
        h_lo, h_hi = 5, 7
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    g = [[7] * w for _ in range(h)]
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    pal = _build_palette(palette_kind, rng)
    color = int(overrides.get("color", rng.choice(pal)))
    corner = (overrides.get("texture") if overrides.get("texture") in CORNERS else None) or \
             overrides.get("corner") or \
             ctx.draw_choice("corner", list(CORNERS))
    if corner == "tl":
        cells = [(0, 0), (0, 1), (1, 0)]
    elif corner == "tr":
        cells = [(0, w - 1), (0, w - 2), (1, w - 1)]
    elif corner == "bl":
        cells = [(h - 1, 0), (h - 1, 1), (h - 2, 0)]
    else:
        cells = [(h - 1, w - 1), (h - 1, w - 2), (h - 2, w - 1)]
    for r, c in cells:
        g[r][c] = color
    return g


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 8, 9]
    pool = [c for c in pool if c != 7]
    rng.shuffle(pool)
    return pool


def _draw_from_degenerate(name, rng):
    h, w = 6, 6
    g = [[7] * w for _ in range(h)]
    if name == "no_corner":
        g[3][3] = 2
        return g
    if name == "all_corners":
        g[0][0] = 2; g[0][w - 1] = 3
        g[h - 1][0] = 4; g[h - 1][w - 1] = 6
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 2
        return g
    return g

def self_check(grid, *, seed=None, sample_index=None, difficulty=None, **kwargs):
    errs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular and nonempty"]
    h, w = len(grid), len(grid[0])
    cells = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] != 7]
    if len(cells) != 3:
        errs.append(f"expected exactly three non-background marker cells, got {len(cells)}")
        return errs
    colors = {v for _, _, v in cells}
    if len(colors) != 1:
        errs.append(f"corner marker cells must share one color, got {colors}")
    rs = [r for r, _, _ in cells]
    cs = [c for _, c, _ in cells]
    corner_shapes = [
        {(0, 0), (0, 1), (1, 0)},
        {(0, w - 1), (0, w - 2), (1, w - 1)},
        {(h - 1, 0), (h - 2, 0), (h - 1, 1)},
        {(h - 1, w - 1), (h - 2, w - 1), (h - 1, w - 2)},
    ]
    if {(r, c) for r, c, _ in cells} not in corner_shapes:
        errs.append("three marker cells should form an L in exactly one corner")
    return errs
