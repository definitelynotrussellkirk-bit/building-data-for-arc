"""Generator for arc_puzzle_bank_21_set13_s:S13_M1.

Rule: a blue-count header chooses the area rank of the body object to crop.

Combinatorial axes (8): grid_h, grid_w, palette_kind, rank,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_marker, tied_areas, more_markers_than_objects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "963dad37593d"
VERSION = "3.1.0"  # add executable invariants for header rank + distinct-area body objects.
TASK_ID = "963dad37593d"
SUMMARY = (
    "0-bg grid with: (a) ROW 0 BLUE HEADER of k color-1 cells (k = rank); "
    "(b) K random body polyominoes with STRICTLY DISTINCT areas, in distinct "
    "colors, 4-connected isolated, placed below the header. Rule: count k blue "
    "cells in row 0; among body objects sorted by AREA DESCENDING (ties by "
    "top-left), select the k-th; crop to bbox and recolor to 8. Object shapes, "
    "areas, count and rank all vary."
)

INVARIANTS = [
    "background is 0",
    "the top row contains k blue cells encoding the rank (1..K)",
    "K body objects with STRICTLY distinct areas",
    "body objects are 4-connected isolated (>=1 gap) and below row 0",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "tied_areas", "more_markers_than_objects")
HELPFUL_TEXTURES = PALETTE_KINDS

RECT_2X3 = [(r, c) for r in range(2) for c in range(3)]
PLUS_5 = [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]
L_3 = [(0, 0), (1, 0), (1, 1)]

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..13", "valid": "9..16"},
    "grid_w":         {"type": "int", "default": "rng 12..15", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "rank":           {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "header_top_objects_below",
                       "valid": "header_top_objects_below"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
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
    if r0 < 1 or c0 < 0 or r0 + sh > h or c0 + sw > w:   # row 0 reserved for header
        return False
    for r in range(max(0, r0 - 1), min(h, r0 + sh + 1)):
        for c in range(max(0, c0 - 1), min(w, c0 + sw + 1)):
            if g[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 10, 12); w = ctx.draw_int("width", 12, 14); K = 3
    elif difficulty == "hard":
        h = ctx.draw_int("height", 13, 16); w = ctx.draw_int("width", 15, 18)
        K = ctx.draw_int("n_objects", 4, 5)
    else:
        h = ctx.draw_int("height", 11, 14); w = ctx.draw_int("width", 13, 16)
        K = ctx.draw_int("n_objects", 3, 4)
    rng = ctx.draw_rng("layout")
    rank = ctx.draw_int("rank", 1, K)
    for _outer in range(40):
        g = full_grid(h, w, 0)
        for c in range(rank):
            g[0][c] = 1
        # K random body polyominoes with STRICTLY distinct areas.
        areas = rng.sample(range(3, 10), K)
        colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], K)
        ok = True
        for area, color in zip(areas, colors):
            shape = _rand_poly(rng, area)
            sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
            placed = False
            for _ in range(80):
                r0 = rng.randint(1, h - sh); c0 = rng.randint(0, w - sw)
                if _free(g, r0, c0, sh, sw):
                    for dr, dc in shape:
                        g[r0 + dr][c0 + dc] = color
                    placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize area-rank layout")


def _draw_from_degenerate(name, rng):
    h, w = 11, 13
    g = full_grid(h, w, 0)
    if name == "no_marker":
        # no blue marker → rank undefined, rule has no selector
        paint_at(g, 2, 1, RECT_2X3, 2)
        paint_at(g, 2, 7, PLUS_5, 3)
        paint_at(g, h - 3, w - 4, L_3, 4)
        return g
    if name == "tied_areas":
        # two body objects same area → rank tie, ambiguous which to crop
        g[0][0] = 1
        paint_at(g, 2, 1, [(0, 0), (0, 1), (1, 0)], 2)
        paint_at(g, 2, 7, [(0, 0), (0, 1), (1, 0)], 3)
        paint_at(g, h - 3, w - 4, L_3, 4)
        return g
    if name == "more_markers_than_objects":
        # 4 markers but only 3 body objects → rank exceeds available
        for c in range(4): g[0][c] = 1
        paint_at(g, 2, 1, RECT_2X3, 2)
        paint_at(g, 2, 7, PLUS_5, 3)
        paint_at(g, h - 3, w - 4, L_3, 4)
        return g
    return g


def _body_components(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    out = []
    for r in range(1, h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 0:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (1 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if not grid:
        return ["empty grid"]
    header_count = sum(1 for v in grid[0] if v == 1)
    if header_count < 1:
        errors.append("top row has no blue rank header")
    if any(v not in (0, 1) for v in grid[0]):
        errors.append("top row contains non-header colors")
    comps = _body_components(grid)
    min_objects = 4 if difficulty == "hard" else 3
    if len(comps) < min_objects:
        errors.append(f"expected at least {min_objects} body objects, found {len(comps)}")
    if header_count > len(comps):
        errors.append("header rank exceeds number of body objects")
    areas = [len(cells) for _, cells in comps]
    if len(areas) != len(set(areas)):
        errors.append("body object areas are not strictly distinct")
    colors = [color for color, _ in comps]
    if len(colors) != len(set(colors)):
        errors.append("body object colors are not distinct")
    return errors
