"""Generator for arc_additional_puzzle_bank_volume11:M75 — pack by descending area.

Rule: colored objects are cropped and packed left-to-right by
descending area.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "843e122e2e8a"
VERSION = "3.0.1"  # FIX: 3 FIXED shapes with FIXED colour<->shape pairing (only placement shuffled) -> area-sorted pack always identical (distinct=1, was flagged intrinsic-low). Now VARIED polyominoes of distinct areas + random distinct colours -> the packed output varies.
TASK_ID = "843e122e2e8a"
SUMMARY = (
    "0-bg grid (h~10-14, w~11-16) with THREE OBJECTS, each a "
    "RANDOM POLYOMINO of a DISTINCT area (areas sampled distinct "
    "from 2..6) in a DISTINCT non-bg colour, scattered at "
    "non-overlapping buffered positions. Rule (CROP EACH OBJECT, "
    "PACK LEFT-TO-RIGHT BY DESCENDING AREA): extract every "
    "4-connected non-bg component, crop to bbox, sort crops by "
    "area descending (ties per demos), pack left-to-right with bg "
    "gaps, bottom-aligned, into a tight output grid. Net: 3 "
    "scattered objects collapse into a horizontal pack ordered "
    "biggest-to-smallest; varied shapes+colours make the pack "
    "differ per sample."
)

INVARIANTS = [
    "background is 0",
    "non-background objects are separated connected components",
    "object areas are distinct",
    "objects use simple polyomino shapes whose crops are nonempty",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_objects", "single_object", "tied_areas")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..14", "valid": "6..24"},
    "grid_w":         {"type": "int", "default": "rng 11..16", "valid": "6..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_objects":      {"type": "int", "default": "3", "valid": "3..3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "scattered_distinct_areas",
                       "valid": "scattered_distinct_areas"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_objects|single_object|tied_areas"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_NONBG = [2, 3, 4, 6, 7, 8, 9]


def _poly(rng, n):
    """A random connected n-cell polyomino, normalized to min (0,0)."""
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < n:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _place(g, cells, color, rng, occ):
    """Place a polyomino at a random non-overlapping, 1-cell-buffered spot."""
    h, w = len(g), len(g[0])
    bh = max(r for r, _ in cells) + 1
    bw = max(c for _, c in cells) + 1
    if bh > h or bw > w:
        return False
    for _ in range(200):
        r0 = rng.randint(0, h - bh); c0 = rng.randint(0, w - bw)
        ac = [(r0 + r, c0 + c) for r, c in cells]
        if any((r + dr, c + dc) in occ
               for r, c in ac for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
            continue
        for r, c in ac:
            g[r][c] = color
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    occ.add((r + dr, c + dc))
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 11); w = ctx.draw_int("grid_w", 11, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 14); w = ctx.draw_int("grid_w", 15, 16)
    else:
        h = ctx.draw_int("grid_h", 10, 14); w = ctx.draw_int("grid_w", 11, 16)
    rng = ctx.draw_rng("placement")

    # 3 DISTINCT areas (so the descending-area sort is unambiguous) and 3
    # DISTINCT colours; each object is a random polyomino of its area.
    areas = rng.sample([2, 3, 4, 5, 6], 3)
    colors = rng.sample(_NONBG, 3)
    # `_place` can fail on unlucky crowded layouts; retry so default data never
    # silently degrades into a 1/2-object packing task.
    for _build in range(80):
        g = full_grid(h, w, 0)
        occ = set()
        ok = True
        for area, color in zip(areas, colors):
            if not _place(g, _poly(rng, area), color, rng, occ):
                ok = False
                break
        if ok and not self_check(g, difficulty=difficulty):
            return g
    raise RuntimeError("failed to place three distinct-area objects")


def _draw_from_degenerate(name, rng):
    h, w = 12, 13
    g = full_grid(h, w, 0)
    if name == "no_objects":
        # blank → nothing to pack
        return g
    if name == "single_object":
        # only one object → packing is trivially identity
        for r, c in [(2, 2), (2, 3), (3, 2), (3, 3)]:
            g[r][c] = 4
        return g
    if name == "tied_areas":
        # two objects with equal area → "descending area" ambiguous
        for r, c in [(2, 2), (2, 3), (3, 2)]: g[r][c] = 3
        for r, c in [(6, 7), (6, 8), (7, 7)]: g[r][c] = 6
        return g
    return g


def _components_nonzero(g):
    h, w = len(g), len(g[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if g[r][c] == 0 or (r, c) in seen:
                continue
            color = g[r][c]
            stack = [(r, c)]; seen.add((r, c)); comp = []
            while stack:
                rr, cc = stack.pop(); comp.append((rr, cc))
                for dr, dc in _CARD:
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and g[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append((color, comp))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    if not isinstance(grid, list) or not grid or not all(isinstance(r, list) and r for r in grid):
        return ["grid must be a nonempty rectangular list"]
    if len({len(r) for r in grid}) != 1:
        return ["grid must be rectangular"]
    vals = {v for row in grid for v in row}
    if 0 not in vals:
        errs.append("background 0 must be present")
    if not vals <= set(range(10)):
        errs.append("cells must be ARC colors 0..9")
    comps = _components_nonzero(grid)
    if len(comps) != 3:
        errs.append("exactly three non-background components required")
    colors = [color for color, _ in comps]
    if len(colors) != len(set(colors)):
        errs.append("objects must use distinct colors")
    areas = [len(comp) for _, comp in comps]
    if len(areas) != len(set(areas)):
        errs.append("object areas must be strictly distinct")
    if any(area < 2 for area in areas):
        errs.append("each object should be a nontrivial polyomino")
    return errs
