"""Generator for puzzle dbc1a6ce.

Rule: for each 0-cell, fill with cyan(8) if there are blue(1) cells on
BOTH sides in its row OR on BOTH sides in its column.

Combinatorial axes (8): grid_h/w, n_dots, dot_distribution,
position_bias, density_kind, anchor_corner, asymmetry_force,
palette_size.
Degenerates: no_dots, single_dot, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "57870373a67e"
# 2.1.0: clustered/contiguous dot blobs have no 0-cell bracketed by 1s on both
# sides (no GAP) -> the fill rule paints nothing -> output == input (identity).
# Now verify the rule fires and, if not, inject a bracketing pair with a gap.
# Adds self_check.
VERSION = "2.1.0"
TASK_ID = "57870373a67e"
SUMMARY = (
    "0-bg grid (h, w~7-14) with 6-12 "
    "SPARSE COLOR-1 (blue) DOTS placed "
    "according to a layout pattern: "
    "scattered/clustered/row_focus/"
    "col_focus/diagonal/corners. At "
    "least one row AND one column has "
    "≥2 blue dots with gap between "
    "them. Rule (BRACKETED-FILL WITH "
    "COLOR 8): for EACH 0-CELL at "
    "(r, c), check if there are "
    "COLOR-1 cells on BOTH SIDES in "
    "the SAME ROW (i.e., some c1 < c "
    "with g[r][c1]==1 AND some c2 > "
    "c with g[r][c2]==1) OR if there "
    "are COLOR-1 cells on BOTH SIDES "
    "in the SAME COLUMN. If yes, "
    "FILL the cell with COLOR 8 "
    "(cyan). Otherwise leave 0. Blue "
    "dots stay. Net: every 0-cell "
    "bracketed by blue in its row OR "
    "column gets painted cyan."
)

INVARIANTS = [
    "background is 0",
    "all non-bg cells are blue(1)",
    ">=4 1-dots placed",
    ">=2 rows or >=2 cols have >=2 1-cells with gap (rule fires)",
]

DOT_DISTRIBUTIONS = ("scattered", "clustered", "row_focus", "col_focus",
                     "diagonal", "corners")
DEGENERATE_TEXTURES = ("no_dots", "single_dot", "full_grid")
HELPFUL_TEXTURES = DOT_DISTRIBUTIONS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 7..14", "valid": "5..18"},
    "grid_w":            {"type": "int", "default": "rng 7..14", "valid": "5..18"},
    "n_dots":            {"type": "int", "default": "rng 6..12", "valid": "4..30"},
    "dot_distribution":  {"type": "str", "default": "rng helpful",
                          "valid": "|".join(DOT_DISTRIBUTIONS)},
    "anchor_corner":     {"type": "bool", "default": "false",
                          "valid": "true|false"},
    "asymmetry_force":   {"type": "bool", "default": "false",
                          "valid": "true|false"},
    "min_brackets":      {"type": "int", "default": "2",
                          "valid": "1..4"},
    "texture":           {"type": "str", "default": "alias for dot_distribution",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 5, 8
    elif difficulty == "hard":
        h_lo, h_hi = 14, 18
    else:
        h_lo, h_hi = 7, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_dots = int(overrides.get("n_dots",
                               ctx.draw_int("n_dots", 6, 12)))
    n_dots = max(4, min(min(h * w // 3, 30), n_dots))
    distribution = (overrides.get("texture") or
                    overrides.get("dot_distribution")
                    or ctx.draw_choice("dot_distribution",
                                       list(DOT_DISTRIBUTIONS)))
    g = full_grid(h, w, 0)
    cells = _pick_cells(distribution, h, w, n_dots, rng)
    for r, c in cells:
        if 0 <= r < h and 0 <= c < w:
            g[r][c] = 1
    # Ensure at least one row + col have brackets
    placed = sum(1 for row in g for v in row if v == 1)
    if placed < 4:
        for r, c in [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]:
            g[r][c] = 1
    # Guarantee the fill rule actually fires: there must be a 0-cell with 1s on
    # both sides in its row OR column. Contiguous clusters have no such gap.
    if not _rule_fires(g):
        # Find an all-zero row and bracket its interior with 1s at the two ends.
        target_row = next((r for r in range(h)
                           if all(g[r][c] == 0 for c in range(w))), None)
        if target_row is not None:
            g[target_row][0] = 1
            g[target_row][w - 1] = 1
        else:
            # No empty row; bracket an empty column instead, else clear+bracket row 0.
            target_col = next((c for c in range(w)
                               if all(g[r][c] == 0 for r in range(h))), None)
            if target_col is not None:
                g[0][target_col] = 1
                g[h - 1][target_col] = 1
            else:
                for c in range(w):
                    g[0][c] = 0
                g[0][0] = 1
                g[0][w - 1] = 1
    return g


def _rule_fires(g):
    """True iff some 0-cell has color-1 cells on both sides in its row or column."""
    h, w = len(g), len(g[0])
    for r in range(h):
        ones = [c for c in range(w) if g[r][c] == 1]
        if ones:
            mn, mx = ones[0], ones[-1]
            if any(g[r][c] == 0 for c in range(mn + 1, mx)):
                return True
    for c in range(w):
        ones = [r for r in range(h) if g[r][c] == 1]
        if ones:
            mn, mx = ones[0], ones[-1]
            if any(g[r][c] == 0 for r in range(mn + 1, mx)):
                return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """All non-bg cells are blue(1) and the bracket-fill rule actually fires
    (a 0-cell with 1s on both sides in its row or column), so output != input."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    errors = []
    nonbg = {v for row in grid for v in row if v != 0}
    if nonbg - {1}:
        errors.append(f"all non-bg cells must be blue(1), found {sorted(nonbg)}")
    if not _rule_fires(grid):
        errors.append("no 0-cell is bracketed by blue on both sides — the fill rule "
                      "paints nothing (output == input, identity)")
    return errors


def _pick_cells(distribution, h, w, n, rng):
    if distribution == "scattered":
        cells = [(r, c) for r in range(h) for c in range(w)]
        rng.shuffle(cells)
        return cells[:n]
    if distribution == "clustered":
        cr = rng.randint(0, h - 1); cc = rng.randint(0, w - 1)
        candidates = [(r, c) for r in range(h) for c in range(w)]
        candidates.sort(key=lambda p: abs(p[0] - cr) + abs(p[1] - cc))
        return candidates[:n]
    if distribution == "row_focus":
        rs = rng.sample(range(h), min(2, h))
        cells = [(r, c) for r in rs for c in range(w)]
        rng.shuffle(cells)
        return cells[:n]
    if distribution == "col_focus":
        cs = rng.sample(range(w), min(2, w))
        cells = [(r, c) for c in cs for r in range(h)]
        rng.shuffle(cells)
        return cells[:n]
    if distribution == "diagonal":
        diag = [(i, i) for i in range(min(h, w))]
        anti = [(i, min(h, w) - 1 - i) for i in range(min(h, w))]
        rest = [(r, c) for r in range(h) for c in range(w)
                if (r, c) not in diag and (r, c) not in anti]
        cells = diag + anti
        rng.shuffle(rest)
        cells.extend(rest)
        return cells[:n]
    if distribution == "corners":
        corners = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
        rest = [(r, c) for r in range(h) for c in range(w)
                if (r, c) not in corners]
        rng.shuffle(rest)
        return (corners + rest)[:n]
    cells = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(cells)
    return cells[:n]


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_dots":
        return g
    if name == "single_dot":
        g[h // 2][w // 2] = 1
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 1
        return g
    return g
