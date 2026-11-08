"""Generator for c87289bb.

Rule: the color-8 columns (cols with 8 in row 0) extend downward from the
bar-row (one above the first color-2 row) to the bottom. For each color-2
segment in the 2-row, walls/bars are drawn around it where the segment's
left/right 8-columns align, and the 8-columns passing through the segment
are blocked (restored to 2 at the 2-row, cleared below).

This generator lays out 8-columns in the top region and color-2 segments
in the 2-row (some aligned with the 8-columns).

Combinatorial axes: grid size, the 8-column positions, the 2-row, and the
segments.
Degenerates: no_eights, no_twos, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "43d815d17b54"
RULE_HASH = "f58e5f2921f0"  # canonical rule this generator was written against
VERSION = "2.0.1"
TASK_ID = "43d815d17b54"
SUMMARY = (
    "0-bg grid (size varies). Color-8 columns in the top region and color-2 "
    "segments in a 2-row. Rule: the 8-columns drop from the bar-row down; "
    "around each 2-segment, walls/bars form where the segment's edge "
    "8-columns align, and 8-columns through the segment are blocked. The "
    "grid size, 8-column positions, 2-row and segments vary freely (was a "
    "fixed setup, ~27 distinct)."
)

INVARIANTS = [
    "color-8 columns are detected from row 0 and extend from the bar-row down",
    "the 2-row is the first row with a color-2; segments are interior",
    "walls/bars form around segments whose edge 8-columns align",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_eights", "no_twos", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "10..18"},
    "n_eight_cols":   {"type": "int", "default": "varies", "valid": "2..6"},
    "n_segments":     {"type": "int", "default": "varies", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "columns_and_segments",
                       "valid": "columns_and_segments"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_eights|no_twos|full_grid"},
}


def _apply(g):
    """Faithful reimplementation of the rule (also the verifier)."""
    h = len(g); w = len(g[0])
    eight_cols = [c for c in range(w) if g[0][c] == 8]
    two_row = -1
    for r in range(h):
        if any(g[r][c] == 2 for c in range(w)):
            two_row = r; break
    bar_row = two_row - 1
    segs = []; c = 0
    while c < w:
        if g[two_row][c] != 2:
            c += 1; continue
        cc = c
        while cc < w and g[two_row][cc] == 2:
            cc += 1
        segs.append((c, cc - 1)); c = cc
    res = {(r, c): g[r][c] for r in range(h) for c in range(w)}
    for col in eight_cols:
        for r in range(bar_row, h):
            res[(r, col)] = 8
    for (l2, r2) in segs:
        seg_e = [c for c in eight_cols if l2 <= c <= r2]
        has_left = bool(seg_e) and min(seg_e) == l2
        has_right = bool(seg_e) and any(c > l2 for c in seg_e)
        left_wall = l2 - 1 if has_left else -1
        right_wall = r2 + 1 if has_right else -1
        if has_left:
            lmin = min(seg_e)
            for r in range(bar_row, h):
                res[(r, left_wall)] = 8
            for c in range(left_wall, lmin + 1):
                res[(bar_row, c)] = 8
        if has_right:
            rmax = max(seg_e)
            for r in range(bar_row, h):
                res[(r, right_wall)] = 8
            for c in range(rmax, right_wall + 1):
                res[(bar_row, c)] = 8
        for c in seg_e:
            res[(two_row, c)] = 2
            for r in range(two_row + 1, h):
                res[(r, c)] = 0
        for c in range(l2, r2 + 1):
            if g[two_row][c] == 2:
                res[(two_row, c)] = 2
    return [[res[(r, c)] for c in range(w)] for r in range(h)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: has color-8 bar columns AND color-2 segment cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    has8 = any(grid[r][c] == 8 for r in range(h) for c in range(w))
    has2 = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    if not has8:
        errs.append("no color-8 bar columns found")
    if not has2:
        errs.append("no color-2 segment cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, er, sr = (9, 11), (10, 13), (2, 3), (1, 2)
    elif difficulty == "hard":
        hr, wr, er, sr = (12, 16), (14, 18), (4, 6), (2, 3)
    else:
        hr, wr, er, sr = (10, 14), (12, 16), (2, 5), (1, 3)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        ne = rng.randint(*er)
        eight_cols = sorted(rng.sample(range(1, w - 1), min(ne, w - 2)))
        two_row = rng.randint(3, h - 3)

        g = full_grid(h, w, 0)
        for r in range(0, two_row - 1):       # top region 8-columns (rows 0..bar_row-1)
            for c in eight_cols:
                g[r][c] = 8

        # 2-segments in the 2-row, interior, some aligned with 8-columns
        occ = set()
        placed = 0
        for _ in range(rng.randint(*sr)):
            length = rng.randint(1, 4)
            if rng.random() < 0.7 and eight_cols:      # align left edge to an 8-column
                l2 = rng.choice(eight_cols)
            else:
                l2 = rng.randint(1, w - 2)
            r2 = min(l2 + length - 1, w - 2)
            if any(c in occ for c in range(l2 - 1, r2 + 2)):
                continue
            for c in range(l2, r2 + 1):
                g[two_row][c] = 2
            for c in range(l2 - 1, r2 + 2):
                occ.add(c)
            placed += 1
        if placed < 1:
            continue
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 12, 0)
    for r in range(0, 4):
        for c in (1, 5, 7, 10):
            g[r][c] = 8
    for c in (1, 2):
        g[5][c] = 2
    for c in (5, 6, 7):
        g[5][c] = 2
    if name == "no_eights":
        g2 = full_grid(10, 12, 0); g2[5][1] = 2
        return g2
    if name == "no_twos":
        for c in range(12):
            g[5][c] = 0
        return g
    if name == "full_grid":
        return full_grid(10, 12, 8)
    return g
