"""Generator for arc_additional_puzzles_21_set5:H32.

Rule: bbox-crop the color-1 cells into mask A and the color-2 cells into
mask B. Align both masks at the top-left and XOR them on a grid of the
max dimensions — cells set in EXACTLY ONE mask become 7, else 0.

Combinatorial axes: grid size, the two shapes (which set the masks) and
their positions.
Degenerates: no_blobs, identical_masks, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "ddfdfd1d29cd"
VERSION = "3.1.0"  # fail-closed on placement exhaustion; add executable XOR-mask invariants.
TASK_ID = "ddfdfd1d29cd"
SUMMARY = (
    "0-bg grid (size varies). ONE color-1 (blue) SHAPE and ONE color-2 "
    "(red) SHAPE (random connected polyominoes whose bbox masks are NOT "
    "identical), placed apart. Rule: bbox-crop each color's cells into a "
    "binary mask, align both masks at the top-left, and XOR them on a "
    "max-dimension grid — cells in exactly one mask become COLOR 7 "
    "(orange). The grid size, the two shapes (which set the XOR) and "
    "their positions all vary freely (was 2 fixed shapes, ~9 distinct)."
)

INVARIANTS = [
    "exactly one color-1 blob and one color-2 blob (each a single component)",
    "their top-left-aligned bbox masks are NOT identical (XOR is non-empty)",
    "the two blobs are placed apart (each color's cells form one bbox)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_blobs", "identical_masks", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_blobs|identical_masks|full_grid"},
}


def _conn_poly(rng, size, maxd):
    for _ in range(80):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        mr = min(r for r, c in cells); mc = min(c for r, c in cells)
        n = [(r - mr, c - mc) for r, c in cells]
        if max(r for r, c in n) < maxd and max(c for r, c in n) < maxd:
            return n
    return [(0, 0), (0, 1), (1, 0)]


def _mask(cells):
    h = max(r for r, c in cells) + 1; w = max(c for r, c in cells) + 1
    m = [[0] * w for _ in range(h)]
    for r, c in cells:
        m[r][c] = 1
    return m


def _reserve(occ, top, left, bh, bw, h, w):
    for r in range(top - 1, top + bh + 1):
        for c in range(left - 1, left + bw + 1):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + bh):
        for c in range(left, left + bw):
            occ[r][c] = True
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, szr, md = (8, 10), (9, 11), (3, 4), 3
    elif difficulty == "hard":
        hr, wr, szr, md = (11, 14), (12, 16), (4, 6), 4
    else:
        hr, wr, szr, md = (9, 12), (10, 14), (3, 5), 4

    for _attempt in range(40):
        s1 = _conn_poly(rng, rng.randint(*szr), md)
        s2 = _conn_poly(rng, rng.randint(*szr), md)
        if _mask(s1) == _mask(s2):     # identical masks → XOR empty
            continue
        h = rng.randint(*hr); w = rng.randint(*wr)
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)

        def _place(cells, color):
            bh = max(r for r, c in cells) + 1; bw = max(c for r, c in cells) + 1
            for _t in range(40):
                top = rng.randint(0, h - bh); left = rng.randint(0, w - bw)
                if _reserve(occ, top, left, bh, bw, h, w):
                    for r, c in cells:
                        g[top + r][left + c] = color
                    return True
            return False

        if _place(s1, 1) and _place(s2, 2):
            return g

    raise ValueError("could not realize two separated non-identical color masks")


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 10, 0)
    if name == "no_blobs":
        return g
    if name == "identical_masks":
        paint_at(g, 1, 1, [(0, 0), (0, 1), (1, 0), (1, 1)], 1)
        paint_at(g, 5, 5, [(0, 0), (0, 1), (1, 0), (1, 1)], 2)
        return g
    if name == "full_grid":
        for r in range(9):
            for c in range(10):
                g[r][c] = 1
        return g
    return g

def _components_of_color(grid, color):
    if not grid or not grid[0]:
        return []
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != color or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def _bbox_mask(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)
    out = [[0 for _ in range(c1 - c0 + 1)] for _ in range(r1 - r0 + 1)]
    for r, c in cells:
        out[r - r0][c - c0] = 1
    return out


def _xor_mask_nonempty(a, b):
    h = max(len(a), len(b))
    w = max(len(a[0]) if a else 0, len(b[0]) if b else 0)
    for r in range(h):
        for c in range(w):
            av = r < len(a) and c < len(a[0]) and a[r][c] == 1
            bv = r < len(b) and c < len(b[0]) and b[r][c] == 1
            if av != bv:
                return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Assert the two source masks are single components and XOR to a visible output."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    vals = {v for row in grid for v in row}
    if vals - {0, 1, 2}:
        errs.append(f"unexpected colors {sorted(vals - {0, 1, 2})}; expected only 0,1,2")
    comps1 = _components_of_color(grid, 1)
    comps2 = _components_of_color(grid, 2)
    if len(comps1) != 1:
        errs.append(f"expected exactly one color-1 component, got {len(comps1)}")
    if len(comps2) != 1:
        errs.append(f"expected exactly one color-2 component, got {len(comps2)}")
    if len(comps1) == 1 and len(comps2) == 1:
        m1 = _bbox_mask(comps1[0])
        m2 = _bbox_mask(comps2[0])
        if m1 == m2:
            errs.append("top-left aligned bbox masks are identical; XOR output would be empty")
        elif not _xor_mask_nonempty(m1, m2):
            errs.append("aligned masks do not produce any XOR-on cells")
    return errs
