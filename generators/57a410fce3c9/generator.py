"""Generator for 758abdf0.

Rule: an all-0 row (or, transposed, an all-0 column) sets the axis. The
first two "mixed" rows (not all-7, not all-0) are marker rows. Per column:
if both marker rows are 8 -> set both to 7 and clear the two opposite-end
rows to 0; if exactly one is 8 -> fill the other with 8.

This generator builds an all-0 row, two marker rows of 8/7, all-7 filler
and opposite rows, then optionally transposes (column-axis variant).

Combinatorial axes: grid size, the per-column marker pattern (both/one/
none), and the orientation.
Degenerates: no_separator, no_markers, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "57a410fce3c9"
VERSION = "2.0.1"  # diversity: random marker pattern + orientation (was fixed ~25)
TASK_ID = "57a410fce3c9"
SUMMARY = (
    "Mostly-7 grid (size varies) with an all-0 separator row/column and two "
    "marker rows holding color-8 markers. Rule: per column, both markers -> "
    "clear both to 7 and zero the two opposite-end rows; one marker -> fill "
    "the other. The grid size, per-column marker pattern and orientation "
    "vary freely (was a fixed setup, ~25 distinct)."
)

INVARIANTS = [
    "an all-0 row (or transposed column) is the only zero line",
    "the two marker rows are the first two mixed rows; opposite rows are all-7",
    "each column transforms by its both/one/none marker pattern",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_separator", "no_markers", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "6..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "6..16"},
    "orientation":    {"type": "str", "default": "rng", "valid": "row|col"},
    "marker_density": {"type": "str", "default": "mixed", "valid": "mixed"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "separator_top", "valid": "separator_top"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_separator|no_markers|full_grid"},
}


def _apply(g):
    """Faithful reimplementation of the rule (also the verifier)."""
    h = len(g); w = len(g[0])
    zero_row = next((r for r in range(h) if all(g[r][c] == 0 for c in range(w))), None)
    zero_col = None
    if zero_row is None:
        zero_col = next((c for c in range(w) if all(g[r][c] == 0 for r in range(h))), None)
    transposed = zero_col is not None
    gg = [[g[r][c] for r in range(h)] for c in range(w)] if transposed else [row[:] for row in g]
    h2 = len(gg); w2 = len(gg[0])
    zr = zero_col if transposed else zero_row
    prows = [r for r in range(h2)
             if not all(gg[r][c] == 7 for c in range(w2))
             and not all(gg[r][c] == 0 for c in range(w2))]
    pr1, pr2 = prows[0], prows[1]
    opp1 = h2 - 2 if zr == 0 else 0
    opp2 = h2 - 1 if zr == 0 else 1
    res = {(r, c): gg[r][c] for r in range(h2) for c in range(w2)}
    for c in range(w2):
        in1 = gg[pr1][c] == 8; in2 = gg[pr2][c] == 8
        if in1 and in2:
            res[(pr1, c)] = 7; res[(pr2, c)] = 7
            res[(opp1, c)] = 0; res[(opp2, c)] = 0
        elif in1:
            res[(pr2, c)] = 8
        elif in2:
            res[(pr1, c)] = 8
    out = [[res[(r, c)] for c in range(w2)] for r in range(h2)]
    if transposed:
        out = [[out[c][r] for c in range(h2)] for r in range(w2)]
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    orient = overrides.get("orientation") or rng.choice(["row", "col"])

    if difficulty == "easy":
        hr, wr = (6, 9), (6, 9)
    elif difficulty == "hard":
        hr, wr = (12, 16), (12, 16)
    else:
        hr, wr = (8, 13), (8, 13)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        if h < 5 or w < 3:
            continue
        # zero-row frame: row 0 all 0, rows 1,2 markers, rest all 7
        g = [[7] * w for _ in range(h)]
        for c in range(w):
            g[0][c] = 0
        any_marker = False
        m1 = [7] * w; m2 = [7] * w
        for c in range(w):
            mode = rng.choice(["both", "one1", "one2", "none", "none"])
            if mode == "both":
                m1[c] = 8; m2[c] = 8; any_marker = True
            elif mode == "one1":
                m1[c] = 8; any_marker = True
            elif mode == "one2":
                m2[c] = 8; any_marker = True
        if not any_marker:
            continue
        # both marker rows must be MIXED (>=1 eight AND >=1 seven) so both are
        # "pattern rows" -> the rule's pr1/pr2 both exist
        if not (8 in m1 and 7 in m1 and 8 in m2 and 7 in m2):
            continue
        g[1] = m1; g[2] = m2

        if orient == "col":
            g = [[g[r][c] for r in range(h)] for c in range(w)]   # transpose
        return g

    return g   # fallback (rare)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: grid has an all-0 row or column (separator) and at least one color-8 marker."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    has_zero_row = any(all(grid[r][c] == 0 for c in range(w)) for r in range(h))
    has_zero_col = any(all(grid[r][c] == 0 for r in range(h)) for c in range(w))
    if not (has_zero_row or has_zero_col):
        errs.append("no all-0 separator row or column found")
    has8 = any(grid[r][c] == 8 for r in range(h) for c in range(w))
    if not has8:
        errs.append("no color-8 marker found")
    return errs


def _draw_from_degenerate(name, rng):
    g = [[7] * 8 for _ in range(8)]
    for c in range(8):
        g[0][c] = 0
    g[1][1] = 8; g[2][1] = 8       # both
    g[1][3] = 8                    # one
    if name == "no_separator":
        for c in range(8):
            g[0][c] = 7
        return g
    if name == "no_markers":
        g[1][1] = 7; g[2][1] = 7; g[1][3] = 7
        return g
    if name == "full_grid":
        return full_grid(8, 8, 7)
    return g
