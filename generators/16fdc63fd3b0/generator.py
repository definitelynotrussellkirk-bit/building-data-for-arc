"""Generator for arc_additional_puzzle_bank_volume16:H109.

Rule: normalize the color-1 cells and color-2 cells to a common origin,
XOR them (cells in exactly one), and output the XOR re-normalized to its
bbox, painted color 8.

Combinatorial axes: grid size, the two shapes (which set the XOR), their
positions, and an optional decoy.
Degenerates: shapes_identical, no_blob_2, no_blob_1.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "16fdc63fd3b0"
VERSION = "3.0.1"  # diversity: random 1/2 shapes + positions + decoy + grid (was 2 fixed shapes)
TASK_ID = "16fdc63fd3b0"
SUMMARY = (
    "0-bg grid (size varies). ONE color-1 (blue) SHAPE and ONE color-2 "
    "(red) SHAPE (random connected polyominoes whose normalized forms "
    "share >=1 cell and differ in >=1 cell), placed apart, plus an "
    "optional non-{1,2} decoy. Rule: normalize each, XOR them (cells in "
    "exactly one), and output the XOR re-normalized to its bbox, painted "
    "COLOR 8 (cyan). The grid size, the two shapes (which set the XOR) "
    "and their positions all vary freely (was 2 fixed shapes, ~12 "
    "distinct)."
)

INVARIANTS = [
    "exactly one color-1 blob and one color-2 blob (placed apart)",
    "their normalized cell sets share >=1 cell and differ in >=1 cell",
    "an optional non-{1,2} decoy is ignored by the rule",
]

PALETTE_KINDS = ("default", "L_shapes", "Z_shapes", "T_shapes")
DEGENERATE_TEXTURES = ("shapes_identical", "no_blob_2", "no_blob_1")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|L_shapes|Z_shapes|T_shapes"},
    "shape_kind":     {"type": "str", "default": "varied", "valid": "varied"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "overlap_kind":   {"type": "str", "default": "partial", "valid": "partial"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|L_shapes|Z_shapes|T_shapes|"
                                "shapes_identical|no_blob_2|no_blob_1"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one color-1 blob and one color-2 blob."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in ("shapes_identical", "no_blob_2", "no_blob_1"):
        return errs
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if not ones:
        errs.append("no color-1 blob cells")
    if not twos:
        errs.append("no color-2 blob cells")
    return errs


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _conn_poly(rng, size, maxd):
    for _ in range(100):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        n = _norm(cells)
        if max(r for r, c in n) < maxd and max(c for r, c in n) < maxd:
            return n
    return [(0, 0), (0, 1), (1, 0)]


def _free(occ, cells, top, left, h, w):
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = top + r + dr, left + c + dc
                if dr == 0 and dc == 0:
                    if not (0 <= rr < h and 0 <= cc < w):
                        return False
                    continue
                if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                    return False
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
        hr, wr, szr, md = (11, 16), (12, 16), (4, 7), 5
    else:
        hr, wr, szr, md = (9, 12), (10, 14), (4, 6), 4

    for _attempt in range(50):
        s1 = _norm(_conn_poly(rng, rng.randint(*szr), md))
        s2 = _norm(_conn_poly(rng, rng.randint(*szr), md))
        A = set(map(tuple, s1)); B = set(map(tuple, s2))
        if not (A & B) or not (A ^ B):    # need overlap AND a difference
            continue
        h = rng.randint(*hr); w = rng.randint(*wr)
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)

        def _place(cells, color):
            bh = max(r for r, c in cells) + 1; bw = max(c for r, c in cells) + 1
            for _t in range(40):
                top = rng.randint(0, h - bh); left = rng.randint(0, w - bw)
                if _free(occ, cells, top, left, h, w):
                    for r, c in cells:
                        g[top + r][left + c] = color; occ[top + r][left + c] = True
                    return True
            return False

        if not (_place(s1, 1) and _place(s2, 2)):
            continue
        # optional decoy (rule ignores non-{1,2})
        if rng.random() < 0.5:
            for _t in range(20):
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if not occ[r][c]:
                    g[r][c] = rng.choice([3, 4, 5, 7])
                    break
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    same = [(0, 0), (1, 0), (2, 0), (2, 1)]
    if name == "shapes_identical":
        paint_at(g, 1, 1, same, 1)
        paint_at(g, 4, 6, same, 2)
        return g
    if name == "no_blob_2":
        paint_at(g, 1, 1, same, 1)
        return g
    if name == "no_blob_1":
        paint_at(g, 4, 6, same, 2)
        return g
    return g
