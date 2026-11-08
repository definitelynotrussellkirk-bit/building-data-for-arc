"""Generator for arc_puzzle_bank_next21:H12 — pack the 4 smallest objects into a 2x2 gallery.

Rule (verified against canonical): take the objects, sort by (size, then bbox
height, bbox width, color), take the FIRST 4, and arrange them in a 2x2 quadrant
layout (a=TL, b=TR, c=BL, d=BR in sorted order) separated by one blank row and
one blank column, each in its own color. Output is that compact 2x2 gallery.

This generator scatters exactly 4 separated single-color objects on a plain grid;
the rule packs them.

Combinatorial axes: grid size, the 4 object shapes/sizes/colors, positions.
Degenerates: too_few_objects, single_object, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e2e3a3d05998"
VERSION = "2.0.0"  # WRONG-TASK rewrite. Docstring/structure claimed '6 panels separated by 9-cols' but the rule packs the 4 smallest scattered objects into a 2x2 gallery; canonical has 4 plain scattered objects, NO 9-dividers (the gen's dividers are spurious extra objects). Now scatter exactly 4 separated single-color objects on a plain grid.
TASK_ID = "e2e3a3d05998"

SUMMARY = (
    "0-bg grid with exactly 4 separated single-color objects (random "
    "polyominoes, 1-5 cells, distinct colors) at random positions. Rule: sort "
    "objects by (size, bbox-h, bbox-w, color), take the first 4, and arrange "
    "them in a 2x2 quadrant gallery separated by one blank row + column, each in "
    "its own color. Net: scattered objects gather into a compact 2x2 layout."
)

INVARIANTS = [
    "background is 0",
    "exactly 4 separated single-color objects (distinct 4-connected components)",
    "objects are small polyominoes (1-5 cells) so the gallery is compact",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("too_few_objects", "single_object", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "6..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "obj_size_max":   {"type": "int", "default": "rng 3..5", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4..4"},
    "position_bias":  {"type": "str", "default": "four_scattered_objects",
                       "valid": "four_scattered_objects"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|too_few_objects|single_object|full_grid"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _free(g, r0, c0, cells):
    h, w = len(g), len(g[0])
    for r, c in cells:
        rr, cc = r0 + r, c0 + c
        if not (0 <= rr < h and 0 <= cc < w):
            return False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = rr + dr, cc + dc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9); w = ctx.draw_int("grid_w", 9, 10); smax = 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16); w = ctx.draw_int("grid_w", 12, 18); smax = 5
    else:
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 10, 14); smax = 5
    rng = ctx.draw_rng("layout")

    for _attempt in range(40):
        g = full_grid(h, w, 0)
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 4)
        placed = 0
        for i in range(4):
            shape = _poly(rng, rng.randint(1, smax))
            sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
            done = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if _free(g, r0, c0, shape):
                    for r, c in shape:
                        g[r0 + r][c0 + c] = colors[i]
                    placed += 1; done = True; break
            if not done:
                break
        if placed == 4:
            return g
    return g   # fallback


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 10, 0)
    if name == "too_few_objects":
        g[1][1] = 2; g[4][4] = 3; g[6][7] = 4   # only 3 objects
        return g
    if name == "single_object":
        g[3][3] = 5; g[3][4] = 5
        return g
    if name == "full_grid":
        for r in range(8):
            for c in range(10):
                g[r][c] = 3
        return g
    return g

def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 0:
                continue
            color = grid[r][c]
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in _CARD:
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append((color, cells))
    return out

def self_check(grid, *, difficulty=None, meta=None):
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    comps = _components(grid)
    errs = []
    if len(comps) != 4:
        errs.append(f"expected exactly four objects, got {len(comps)}")
    if len({color for color, _ in comps}) != len(comps):
        errs.append("object colors must be distinct")
    for color, cells in comps:
        if len(cells) > 5:
            errs.append(f"color {color} object has {len(cells)} cells, expected <=5")
    return errs
