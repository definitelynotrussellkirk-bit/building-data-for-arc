"""Generator for arc_additional_puzzle_bank_volume10:H68.

Rule: among the blue (color-1) objects, find the one whose normalized
shape is UNIQUE (appears exactly once; all other shapes are duplicated),
scale it 2x, and output it in color 8.

This generator places M common shapes (each >=2 copies) plus exactly one
unique shape, all in blue, separated.

Combinatorial axes: grid size, the unique shape, the common
shapes/counts, and positions.
Degenerates: all_same_shape, all_unique, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "4a1513fe3fe9"
# 3.1.0: defect-lint all_background_output — the UNIQUE shape could be a solid
# bar/rect, whose 2x-upscaled output is a featureless block; it is now redrawn
# until it doesn't fill its bbox. (3.0.1: larger oriented unique shapes + decoys.)
VERSION = "3.1.0"
TASK_ID = "4a1513fe3fe9"
SUMMARY = (
    "0-bg grid (size varies) with blue (color-1) objects: M common shapes "
    "(each >=2 copies) plus exactly one UNIQUE shape. Rule: find the unique "
    "shape, scale it 2x, output in color 8. The grid size, unique shape, "
    "common shapes/counts and positions vary freely (was a fixed setup, ~21 "
    "distinct)."
)

INVARIANTS = [
    "all objects are blue; exactly one shape appears once, the rest are duplicated",
    "the unique shape's normalized form differs from every common shape",
    "the output is the 2x upscale of the unique shape in color 8",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_same_shape", "all_unique", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "n_common":       {"type": "int", "default": "varies", "valid": "1..3"},
    "unique_size":    {"type": "int", "default": "varies", "valid": "3..7"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|all_same_shape|all_unique|no_blobs"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


def _orient(rng, cells):
    """Apply a random dihedral transform (rotation/reflection) and normalize.
    same-shape? is translation-exact, so each orientation is a distinct shape
    -> this multiplies the distinct 2x-scaled outputs."""
    k = rng.randint(0, 7)
    out = []
    for (r, c) in cells:
        if k & 1:
            r, c = c, r            # transpose
        if k & 2:
            r = -r                 # flip vertical
        if k & 4:
            c = -c                 # flip horizontal
        out.append((r, c))
    return _norm(out)


def _reserve(occ, top, left, sh, sw, h, w, margin=1):
    for r in range(top - margin, top + sh + margin):
        for c in range(left - margin, left + sw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + sh):
        for c in range(left, left + sw):
            occ[r][c] = True
    return True


def _place(rng, g, occ, cells, h, w, color=1):
    sh = max(r for r, c in cells) + 1; sw = max(c for r, c in cells) + 1
    if sh > h or sw > w:
        return False
    for _t in range(50):
        top = rng.randint(0, h - sh); left = rng.randint(0, w - sw)
        if _reserve(occ, top, left, sh, sw, h, w):
            paint_at(g, top, left, cells, color)
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, mr, us = (12, 14), (12, 15), (1, 2), (3, 6)
    elif difficulty == "hard":
        hr, wr, mr, us = (17, 22), (18, 24), (2, 3), (6, 9)
    else:
        hr, wr, mr, us = (13, 18), (14, 20), (1, 3), (4, 8)

    for _attempt in range(40):
        M = rng.randint(*mr)
        commons = []
        seen_norms = set()
        for _ in range(M):
            for _t in range(40):
                sp = _poly(rng, rng.randint(3, 6))
                key = tuple(sp)
                if key not in seen_norms:
                    seen_norms.add(key); commons.append(sp); break
        if len(commons) < M:
            continue
        # unique shape (randomly oriented), distinct from every common and NOT
        # a solid bbox-filler (its 2x upscale would be a featureless block)
        uniq = None
        for _t in range(60):
            sp = _orient(rng, _poly(rng, rng.randint(*us)))
            sh_ = max(r for r, _ in sp) + 1
            sw_ = max(c for _, c in sp) + 1
            if len(set(sp)) == sh_ * sw_:
                continue
            if tuple(sp) not in seen_norms:
                uniq = sp; break
        if uniq is None:
            continue

        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        ok = True
        for sp in commons:
            ncopy = rng.randint(2, 3)
            for _ in range(ncopy):
                if not _place(rng, g, occ, sp, h, w):
                    ok = False; break
            if not ok:
                break
        if not ok:
            continue
        if not _place(rng, g, occ, uniq, h, w):
            continue
        # canonical rule-ignored decoy objects in colors {6,7} (match the
        # canonical input distribution; the rule only reads color-1 objects).
        for _ in range(rng.randint(1, 3)):
            dc = rng.choice([6, 7])
            _place(rng, g, occ, _poly(rng, rng.randint(2, 5)), h, w, color=dc)
        return g

    return g   # fallback (rare)




def _blue_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in _CARD:
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == 1:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    from collections import Counter
    comps = _blue_components(grid)
    if len(comps) < 3:
        return [f"expected duplicated blue shapes plus one unique, got {len(comps)} components"]
    shapes = Counter(tuple(_norm(cells)) for cells in comps)
    singles = [shape for shape, count in shapes.items() if count == 1]
    errors = []
    if len(singles) != 1:
        errors.append(f"expected exactly one unique normalized blue shape, got {len(singles)}")
    if any(count < 2 for shape, count in shapes.items() if shape not in singles):
        errors.append(f"non-unique shapes should be duplicated, got counts {dict(shapes)}")
    return errors

def _draw_from_degenerate(name, rng):
    g = full_grid(12, 12, 0)
    a = [(0, 0), (0, 1), (1, 0)]
    b = [(0, 0), (1, 0), (2, 0)]
    paint_at(g, 1, 1, a, 1)
    paint_at(g, 1, 6, a, 1)
    if name == "all_same_shape":
        paint_at(g, 6, 1, a, 1)
        return g
    if name == "no_blobs":
        return full_grid(12, 12, 0)
    if name == "all_unique":
        g2 = full_grid(12, 12, 0)
        paint_at(g2, 1, 1, a, 1)
        paint_at(g2, 6, 1, b, 1)
        return g2
    paint_at(g, 6, 1, b, 1)   # unique
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; color-1 objects present; at least 2 color-1 connected components."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    seen = [[False] * w for _ in range(h)]
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 1 and not seen[r][c]:
                stack = [(r, c)]
                seen[r][c] = True
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 1 and not seen[nr][nc]:
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                components.append(cells)
    if len(components) < 2:
        errors.append(f"expected >=2 color-1 objects, found {len(components)}")
    return errors
