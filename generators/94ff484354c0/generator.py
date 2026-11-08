"""Generator for v1_e_m_h_keys:M3 — connect each same-color pair with a row/col line.

Rule: each non-bg color has exactly 2 markers in the same row or
column. Output paints the segment between (and including) them with
that color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_colors,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, single_marker, collinear_zero_gap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.palette import random_palette

GENERATOR_ID = "94ff484354c0"
VERSION = "1.2.0"
TASK_ID = "94ff484354c0"
SUMMARY = "1-3 distinct colors, each with exactly 2 markers in a shared row or column."

INVARIANTS = [
    "background is 0",
    "1-3 distinct colors, each with exactly 2 markers",
    "every pair shares a row or column with ≥1 0-cell strictly between",
    "pairs use distinct rows and distinct cols (segments don't cross)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "single_marker", "collinear_zero_gap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 6..9", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_colors":       {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "position_bias":  {"type": "str", "default": "row_col_pairs",
                       "valid": "row_col_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _row_segment(r, c1, c2):
    return {(r, c) for c in range(c1, c2 + 1)}


def _col_segment(c, r1, r2):
    return {(r, c) for r in range(r1, r2 + 1)}


def _fallback_grid(h, w, colors):
    g = full_grid(h, w, 0)
    for i, color in enumerate(colors):
        r = min(h - 1, i * 2)
        # Keep a visible 0-gap and avoid adjacent endpoints.  Reusing columns
        # across different rows is fine because row segments do not cross.
        c1 = 0
        c2 = min(w - 1, max(2, w - 1 - (i % 2)))
        if c2 - c1 < 2:
            c2 = min(w - 1, c1 + 2)
        g[r][c1] = color
        g[r][c2] = color
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 6, 7)
        n_colors = ctx.draw_int("n_colors", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
        n_colors = ctx.draw_int("n_colors", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 6, 9)
        n_colors = ctx.draw_int("n_colors", 1, 3)
    rng = ctx.draw_rng("layout")
    colors = list(random_palette(rng, n_colors))
    for _layout_attempt in range(80):
        g = full_grid(h, w, 0)
        busy_rows: set[int] = set()
        busy_cols: set[int] = set()
        # Reserve the full would-be painted segment, not just the two markers.
        # Otherwise a later marker can land in an earlier pair's gap, making the
        # Racket rule's "only zeros between endpoints" guard reject that pair.
        reserved: set[tuple[int, int]] = set()
        placed = 0
        for color in colors:
            ok = False
            for _ in range(120):
                if rng.random() < 0.5:
                    r = rng.randint(0, h - 1)
                    if r in busy_rows:
                        continue
                    cs = sorted(rng.sample(range(w), 2))
                    if cs[1] - cs[0] < 2:
                        continue
                    if cs[0] in busy_cols or cs[1] in busy_cols:
                        continue
                    seg = _row_segment(r, cs[0], cs[1])
                    if seg & reserved:
                        continue
                    g[r][cs[0]] = color; g[r][cs[1]] = color
                    busy_rows.add(r)
                    reserved |= seg
                    ok = True
                    break
                else:
                    c = rng.randint(0, w - 1)
                    if c in busy_cols:
                        continue
                    rs = sorted(rng.sample(range(h), 2))
                    if rs[1] - rs[0] < 2:
                        continue
                    if rs[0] in busy_rows or rs[1] in busy_rows:
                        continue
                    seg = _col_segment(c, rs[0], rs[1])
                    if seg & reserved:
                        continue
                    g[rs[0]][c] = color; g[rs[1]][c] = color
                    busy_cols.add(c)
                    reserved |= seg
                    ok = True
                    break
            if not ok:
                break
            placed += 1
        if placed == len(colors):
            return g
    return _fallback_grid(h, w, colors)


def _draw_from_degenerate(name, rng):
    h, w = 7, 7
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # Lone markers — no two share a row or column for the rule to connect.
        g[1][3] = 4; g[5][6] = 5
        return g
    if name == "single_marker":
        # Color has only one marker — pair connection has no second endpoint.
        g[2][2] = 4
        return g
    if name == "collinear_zero_gap":
        # Pair adjacent in row — zero gap between them, segment is just the two cells.
        g[2][2] = 4; g[2][3] = 4
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    by_color = {}
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == 0:
                continue
            by_color.setdefault(v, []).append((r, c))
    if not by_color:
        return ["no marker pairs"]
    if difficulty == "hard" and len(by_color) < 2:
        errs.append("hard instance has fewer than two color pairs")
    for color, pts in by_color.items():
        if len(pts) != 2:
            errs.append(f"color {color} has {len(pts)} markers, expected 2")
            continue
        (r1, c1), (r2, c2) = sorted(pts)
        if r1 != r2 and c1 != c2:
            errs.append(f"color {color} pair is not row/col aligned")
            continue
        if r1 == r2:
            lo, hi = sorted((c1, c2))
            if hi - lo < 2:
                errs.append(f"color {color} row pair has no zero gap")
            if any(grid[r1][c] != 0 for c in range(lo + 1, hi)):
                errs.append(f"color {color} row pair gap is blocked")
        else:
            lo, hi = sorted((r1, r2))
            if hi - lo < 2:
                errs.append(f"color {color} col pair has no zero gap")
            if any(grid[r][c1] != 0 for r in range(lo + 1, hi)):
                errs.append(f"color {color} col pair gap is blocked")
    return errs
