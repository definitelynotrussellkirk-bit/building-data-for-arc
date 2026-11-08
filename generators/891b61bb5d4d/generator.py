"""Generator for arc_additional_puzzle_bank_volume14:M96.

Rule: the two blue(1) cells define bbox A; the two red(2) cells define
bbox B. Paint the RECTANGLE INTERSECTION of A and B with color 8 (only
when the intersection is non-empty; else the grid is unchanged).

Combinatorial axes: grid size, the two rects (corner positions, sizes,
aspect), the guaranteed shared region, and the decoration.
Degenerates: no_overlap, no_rect_1, no_rect_2.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "891b61bb5d4d"
VERSION = "2.0.1"  # diversity: random rects + guaranteed overlap + grid (was fixed layout)
TASK_ID = "891b61bb5d4d"
SUMMARY = (
    "0-bg grid (size varies). Exactly TWO blue(1) cells at distinct rows "
    "AND distinct cols define BBOX A; exactly TWO red(2) cells likewise "
    "define BBOX B. The two bboxes are built around a shared anchor so "
    "they overlap. Rule: paint the RECTANGLE INTERSECTION of A and B with "
    "COLOR 8 (cyan). A non-{1,2} decoration sits outside both rects. The "
    "grid size, the two rects (corner positions / sizes / aspect) and the "
    "decoration all vary freely (was a fixed 2+2 cell layout)."
)

INVARIANTS = [
    "exactly 2 blue(1) cells at distinct rows AND distinct cols",
    "exactly 2 red(2) cells at distinct rows AND distinct cols",
    "the two bboxes overlap in at least one cell (non-empty intersection)",
    "decoration is a non-{1,2} cell",
]

PALETTE_KINDS = ("default", "small_overlap", "large_overlap", "edge_overlap")
DEGENERATE_TEXTURES = ("no_overlap", "no_rect_1", "no_rect_2")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|small_overlap|large_overlap|edge_overlap"},
    "overlap_size":   {"type": "str", "default": "varies", "valid": "varies"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "rect_aspect":    {"type": "str", "default": "varies", "valid": "varies"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|small_overlap|large_overlap|edge_overlap|"
                                "no_overlap|no_rect_1|no_rect_2"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 2 blue(1) cells at distinct rows+cols; 2 red(2) cells; bboxes overlap."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if not ones:
        return []  # degenerate no_rect_1 — allowed
    if not twos:
        return []  # degenerate no_rect_2 — allowed
    errs = []
    if len(ones) != 2:
        errs.append(f"expected exactly 2 blue(1) cells; found {len(ones)}")
    else:
        (r1a, c1a), (r1b, c1b) = ones
        if r1a == r1b or c1a == c1b:
            errs.append("blue(1) corners are collinear (same row or col)")
    if len(twos) != 2:
        errs.append(f"expected exactly 2 red(2) cells; found {len(twos)}")
    else:
        (r2a, c2a), (r2b, c2b) = twos
        if r2a == r2b or c2a == c2b:
            errs.append("red(2) corners are collinear (same row or col)")
    if errs:
        return errs
    # Check overlap
    a_r1, a_r2 = min(r1a, r1b), max(r1a, r1b)
    a_c1, a_c2 = min(c1a, c1b), max(c1a, c1b)
    b_r1, b_r2 = min(r2a, r2b), max(r2a, r2b)
    b_c1, b_c2 = min(c2a, c2b), max(c2a, c2b)
    ir1, ir2 = max(a_r1, b_r1), min(a_r2, b_r2)
    ic1, ic2 = max(a_c1, b_c1), min(a_c2, b_c2)
    if ir1 > ir2 or ic1 > ic2:
        return []  # degenerate no_overlap — allowed
    return errs


def _rect_around(rng, pr, pc, h, w, span):
    """A bbox [r0,r1]x[c0,c1] containing (pr,pc), each side >=2, within bounds."""
    rh = rng.randint(2, span)
    above = rng.randint(0, rh - 1)
    r0 = max(0, pr - above)
    r1 = min(h - 1, r0 + rh - 1)
    r0 = max(0, r1 - (rh - 1))
    if r1 == r0:                       # forced flat by bounds: widen if possible
        if r1 + 1 < h:
            r1 += 1
        elif r0 > 0:
            r0 -= 1
    cw = rng.randint(2, span)
    left = rng.randint(0, cw - 1)
    c0 = max(0, pc - left)
    c1 = min(w - 1, c0 + cw - 1)
    c0 = max(0, c1 - (cw - 1))
    if c1 == c0:
        if c1 + 1 < w:
            c1 += 1
        elif c0 > 0:
            c0 -= 1
    return r0, c0, r1, c1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, span = (9, 10), (11, 12), 4
    elif difficulty == "hard":
        hr, wr, span = (12, 16), (13, 16), 7
    else:
        hr, wr, span = (9, 12), (11, 14), 5

    for _attempt in range(60):
        h = rng.randint(*hr); w = rng.randint(*wr)
        # shared anchor — guarantees the two bboxes intersect there
        pr = rng.randint(1, h - 2); pc = rng.randint(1, w - 2)

        ar0, ac0, ar1, ac1 = _rect_around(rng, pr, pc, h, w, span)
        br0, bc0, br1, bc1 = _rect_around(rng, pr, pc, h, w, span)

        # both rects must be genuine (distinct rows AND cols)
        if ar0 == ar1 or ac0 == ac1 or br0 == br1 or bc0 == bc1:
            continue

        # blue(1) corners (one diagonal) and red(2) corners (other diagonal)
        ones = [(ar0, ac0), (ar1, ac1)]
        twos = [(br0, bc1), (br1, bc0)]
        # the 4 corner positions must be distinct, else a color gets <2 cells
        if len(set(ones + twos)) != 4:
            continue

        g = full_grid(h, w, 0)
        for r, c in ones:
            g[r][c] = 1
        for r, c in twos:
            g[r][c] = 2

        # decoration: a non-{1,2} color placed OUTSIDE both bboxes if possible
        deco_color = rng.choice([3, 4, 5, 7])
        for _t in range(40):
            dr = rng.randint(0, h - 1); dc = rng.randint(0, w - 1)
            if g[dr][dc] != 0:
                continue
            in_a = ar0 <= dr <= ar1 and ac0 <= dc <= ac1
            in_b = br0 <= dr <= br1 and bc0 <= dc <= bc1
            if in_a or in_b:
                continue
            g[dr][dc] = deco_color
            break

        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_overlap":
        # two rects that don't intersect → bbox intersection is empty
        g[1][1] = 1; g[2][3] = 1
        g[6][7] = 2; g[8][10] = 2
        g[h - 1][w - 1] = 5
        return g
    if name == "no_rect_1":
        # only 2-cells; no 1-rect → rule no-ops
        g[3][4] = 2; g[7][9] = 2
        g[h - 1][w - 1] = 5
        return g
    if name == "no_rect_2":
        # only 1-cells; no 2-rect → rule no-ops
        g[1][1] = 1; g[6][7] = 1
        g[h - 1][w - 1] = 5
        return g
    return g
