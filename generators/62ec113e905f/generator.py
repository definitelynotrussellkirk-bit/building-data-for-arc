"""Generator for 551d5bf1.

Rule: for each color-1 blob, fill the holes inside its bounding box with 8,
and where the blob does not reach a bbox edge (a gap on the top/bottom/left/
right border), shoot an 8 ray outward from that column/row to the grid edge.

This generator draws several separated color-1 polyominoes (with concavities)
with room around them for the rays.

Combinatorial axes: grid size, number of blobs, blob shapes, and positions.
Degenerates: no_blob, solid_block, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "62ec113e905f"
VERSION = "2.1.0"  # multi-blob default distribution; preserves bbox fill + outward rays
TASK_ID = "62ec113e905f"
SUMMARY = (
    "0-bg grid (size varies) with 2-6 separated color-1 blobs. Rule: fill "
    "each blob's bbox holes with 8 and shoot 8 rays outward from each bbox "
    "edge the blob does not reach. The grid size, blob count, shapes and "
    "positions vary freely."
)

INVARIANTS = [
    "2-6 separated color-1 polyominoes with concavities (bbox holes and/or edge gaps)",
    "bbox holes fill with 8; edge gaps shoot 8 rays to the grid edge",
    "the blob has room around it for the rays",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blob", "solid_block", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "n_blobs":        {"type": "int", "default": "varies", "valid": "2..6"},
    "blob_size":      {"type": "int", "default": "varies", "valid": "5..14"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "centred_blob", "valid": "centred_blob"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_blob|solid_block|full_grid"},
}


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


def _free(g, top, left, shape, *, pad=1):
    h, w = len(g), len(g[0])
    rs = [r for r, _ in shape]; cs = [c for _, c in shape]
    r0, c0 = top + min(rs), left + min(cs)
    r1, c1 = top + max(rs), left + max(cs)
    if r0 - pad < 0 or c0 - pad < 0 or r1 + pad >= h or c1 + pad >= w:
        return False
    for r in range(r0 - pad, r1 + pad + 1):
        for c in range(c0 - pad, c1 + pad + 1):
            if g[r][c] != 0:
                return False
    return True


def _apply(g):
    """Faithful reimplementation of the rule (also the verifier)."""
    h = len(g); w = len(g[0])
    result = {(r, c): g[r][c] for r in range(h) for c in range(w)}
    visited = set()
    for r in range(h):
        for c in range(w):
            if g[r][c] == 1 and (r, c) not in visited:
                st = [(r, c)]; cells = set()
                while st:
                    cr, cc = st.pop()
                    if (cr, cc) in visited or not (0 <= cr < h and 0 <= cc < w) or g[cr][cc] != 1:
                        continue
                    visited.add((cr, cc)); cells.add((cr, cc))
                    st += [(cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)]
                r1 = min(x for x, y in cells); c1 = min(y for x, y in cells)
                r2 = max(x for x, y in cells); c2 = max(y for x, y in cells)
                for fr in range(r1, r2 + 1):
                    for fc in range(c1, c2 + 1):
                        if (fr, fc) not in cells:
                            result[(fr, fc)] = 8
                for gc in range(c1, c2 + 1):
                    if (r1, gc) not in cells:
                        for gr in range(r1 - 1, -1, -1):
                            result[(gr, gc)] = 8
                    if (r2, gc) not in cells:
                        for gr in range(r2 + 1, h):
                            result[(gr, gc)] = 8
                for gr in range(r1, r2 + 1):
                    if (gr, c1) not in cells:
                        for gc in range(c1 - 1, -1, -1):
                            result[(gr, gc)] = 8
                    if (gr, c2) not in cells:
                        for gc in range(c2 + 1, w):
                            result[(gr, gc)] = 8
    return [[result[(r, c)] for c in range(w)] for r in range(h)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, sr, nr = (12, 15), (13, 17), (5, 8), (2, 3)
    elif difficulty == "hard":
        hr, wr, sr, nr = (18, 24), (20, 26), (8, 14), (4, 6)
    else:
        hr, wr, sr, nr = (15, 21), (16, 23), (6, 11), (3, 5)

    fallback = None
    for _attempt in range(80):
        h = rng.randint(*hr)
        w = rng.randint(*wr)
        n_blobs = ctx.draw_int("n_blobs", *nr)
        g = full_grid(h, w, 0)
        placed = 0
        for _blob_i in range(n_blobs):
            shape = _poly(rng, rng.randint(*sr))
            sh = max(r for r, c in shape) + 1
            sw = max(c for r, c in shape) + 1
            if sh + 4 > h or sw + 4 > w:
                continue
            for _place_attempt in range(120):
                top = rng.randint(2, h - sh - 2)
                left = rng.randint(2, w - sw - 2)
                if not _free(g, top, left, shape, pad=1):
                    continue
                paint_at(g, top, left, shape, 1)
                placed += 1
                break
        if placed >= n_blobs and _apply(g) != g:
            return g
        if fallback is None and placed >= 2 and _apply(g) != g:
            fallback = g

    if fallback is not None:
        return fallback
    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 14, 0)
    blob = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)]
    paint_at(g, 4, 5, blob, 1)
    if name == "no_blob":
        return full_grid(12, 14, 0)
    if name == "solid_block":
        g2 = full_grid(12, 14, 0)
        for r in range(4, 7):
            for c in range(5, 8):
                g2[r][c] = 1
        return g2
    if name == "full_grid":
        return full_grid(12, 14, 1)
    return g
def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(v not in (0, 1) for row in grid for v in row):
        errors.append("input should contain only background 0 and blob color 1")
    h, w = len(grid), len(grid[0])
    seen = set(); comps = 0
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            comps += 1
            stack = [(r, c)]; seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                for dr, dc in _CARD:
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 1 and (nr, nc) not in seen:
                        seen.add((nr, nc)); stack.append((nr, nc))
    if comps < 2:
        errors.append(f"expected at least two separated color-1 blobs, got {comps}")
    if comps > 6:
        errors.append(f"expected at most six separated color-1 blobs, got {comps}")
    if _apply(grid) == grid:
        errors.append("blob has no holes/edge gaps; rule output would equal input")
    return errors
