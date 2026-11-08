"""Generator for H149 (c9c4c55a191d).

Rule: treat only color-1 cells as foreground; find the color-1 blobs
(4-connected), rank them by bounding-box AREA (descending), and recolor
the largest 2, the next 3, the next 4, ... on a blank grid.

This generator scatters K connected color-1 blobs with DISTINCT bbox
areas (so the rank is unambiguous) on a 0 background.

Combinatorial axes: grid size, blob count, the blob shapes/sizes, and
their positions.
Degenerates: single_blob, no_blob, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "c9c4c55a191d"
VERSION = "2.0.0"  # diversity: K random distinct-area color-1 blobs + grid (was fixed ~17)
TASK_ID = "c9c4c55a191d"
SUMMARY = (
    "0-bg grid (size varies). K (2-8) connected color-1 BLOBS with distinct "
    "bounding-box areas, scattered apart. Rule: rank the color-1 blobs by "
    "bbox area (descending) and recolor them on a blank grid -- largest 2, "
    "next 3, next 4, ... The grid size, blob count, blob shapes/sizes and "
    "positions vary freely (was a fixed layout, ~17 distinct)."
)

INVARIANTS = [
    "every blob is a single connected color-1 component, separated from the others",
    "all blobs have distinct bounding-box areas (the rank is unambiguous)",
    "the output recolors each blob by descending-area rank starting at 2",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("single_blob", "no_blob", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "n_blobs":        {"type": "int", "default": "varies", "valid": "2..8"},
    "blob_size":      {"type": "int", "default": "varies", "valid": "2..12"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|single_blob|no_blob|full_grid"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


def _bbox_area(shape):
    h = max(r for r, c in shape) + 1; w = max(c for r, c in shape) + 1
    return h * w


def _reserve(occ, top, left, sh, sw, h, w):
    for r in range(top - 1, top + sh + 1):
        for c in range(left - 1, left + sw + 1):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + sh):
        for c in range(left, left + sw):
            occ[r][c] = True
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, nr, sr = (12, 14), (12, 15), (2, 3), (2, 6)
    elif difficulty == "hard":
        hr, wr, nr, sr = (17, 22), (18, 24), (5, 8), (3, 12)
    else:
        hr, wr, nr, sr = (14, 18), (14, 19), (3, 5), (2, 9)

    for _attempt in range(40):
        K = rng.randint(*nr)
        # build K shapes with DISTINCT bbox areas (unambiguous rank)
        shapes = []; areas = set()
        for _t in range(200):
            sp = _poly(rng, rng.randint(*sr))
            a = _bbox_area(sp)
            if a in areas:
                continue
            areas.add(a); shapes.append(sp)
            if len(shapes) == K:
                break
        if len(shapes) < K:
            continue

        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        placed = 0
        for sp in shapes:
            sh = max(r for r, c in sp) + 1; sw = max(c for r, c in sp) + 1
            if sh > h or sw > w:
                continue
            for _p in range(40):
                top = rng.randint(0, h - sh); left = rng.randint(0, w - sw)
                if _reserve(occ, top, left, sh, sw, h, w):
                    paint_at(g, top, left, sp, 1)
                    placed += 1
                    break
        if placed >= 2:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 12, 0)
    if name == "single_blob":
        paint_at(g, 4, 4, [(0, 0), (0, 1), (1, 0), (1, 1)], 1)
        return g
    if name == "no_blob":
        return g
    if name == "full_grid":
        for r in range(12):
            for c in range(12):
                g[r][c] = 1
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    from puzzle_generators.helpers.selfcheck import components_cells, bbox
    errs: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if any(v not in (0, 1) for row in grid for v in row):
        errs.append("normal examples should only use bg=0 and foreground=1")
    comps = components_cells(grid, colors={1})
    if len(comps) < 2:
        errs.append("need at least two color-1 blobs")
    areas = []
    for cells in comps:
        r1, c1, r2, c2 = bbox(cells)
        areas.append((r2 - r1 + 1) * (c2 - c1 + 1))
    if len(set(areas)) != len(areas):
        errs.append("blob bounding-box areas must be distinct")
    return errs
