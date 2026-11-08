"""Generator for bdad9b1f.

Rule: find col with 8s and row with 2s. Output: full col with 8s,
full row with 2s, intersection cell = 4.

Combinatorial axes (8): grid_h/w, n_eights, n_twos, col8_position,
row2_position, position_bias, decoy_density, asymmetry.
Degenerates: no_eights, no_twos, all_intersection.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c99f630b7541"
VERSION = "2.0.0"
TASK_ID = "c99f630b7541"
SUMMARY = (
    "0-bg grid (h~5-12, w~6-14) with: "
    "(a) 2-4 COLOR-8 (cyan) CELLS all "
    "in a SINGLE COLUMN col8 at "
    "DISTINCT ROWS (excluding row2); "
    "(b) 2-4 COLOR-2 (red) CELLS all "
    "in a SINGLE ROW row2 at DISTINCT "
    "COLUMNS (excluding col8). "
    "Positions for col8 and row2 are "
    "biased center/spread/edge. No "
    "other non-bg cells; no color-4 "
    "anywhere. Rule (CROSS COMPLETION "
    "+ INTERSECTION COLOR-4): identify "
    "the COLOR-8 COLUMN and COLOR-2 "
    "ROW. PAINT the ENTIRE col8 column "
    "with COLOR 8 (every cell in that "
    "column, top to bottom). PAINT the "
    "ENTIRE row2 row with COLOR 2 "
    "(every cell in that row, left to "
    "right). At the INTERSECTION cell "
    "(row2, col8), PAINT with COLOR 4 "
    "(yellow). Net: scattered "
    "evidence in one row and one "
    "column → full cross with yellow "
    "intersection."
)

INVARIANTS = [
    "background is 0",
    "all 8-cells share one column",
    "all 2-cells share one row",
    ">=2 8-cells and >=2 2-cells (so the cross is non-trivial)",
    "no other non-bg cells",
    "no 4 in input (rule writes 4 for intersection)",
]

POSITION_BIAS = ("center", "spread", "edge")
DEGENERATE_TEXTURES = ("no_eights", "no_twos", "all_intersection")
HELPFUL_TEXTURES = POSITION_BIAS

AXES = {
    "grid_h":             {"type": "int", "default": "rng 5..12", "valid": "4..16"},
    "grid_w":             {"type": "int", "default": "rng 6..14", "valid": "5..18"},
    "n_eights":           {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "n_twos":             {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "col8_position":      {"type": "str", "default": "rng helpful",
                           "valid": "|".join(POSITION_BIAS)},
    "row2_position":      {"type": "str", "default": "rng helpful",
                           "valid": "|".join(POSITION_BIAS)},
    "asymmetry":          {"type": "bool", "default": "false",
                           "valid": "true|false"},
    "anchor_corner":      {"type": "bool", "default": "false",
                           "valid": "true|false"},
    "texture":            {"type": "str", "default": "alias for col8_position",
                           "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 4, 6, 5, 8
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 11, 16, 13, 18
    else:
        h_lo, h_hi, w_lo, w_hi = 5, 12, 6, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_eights = int(overrides.get("n_eights",
                                 ctx.draw_int("n_eights", 2, 4)))
    n_twos = int(overrides.get("n_twos",
                               ctx.draw_int("n_twos", 2, 4)))
    n_eights = max(2, min(h - 1, n_eights))
    n_twos = max(2, min(w - 1, n_twos))
    col8_pos = (overrides.get("texture") or
                overrides.get("col8_position")
                or ctx.draw_choice("col8_position", list(POSITION_BIAS)))
    row2_pos = overrides.get("row2_position",
                             ctx.draw_choice("row2_position",
                                             list(POSITION_BIAS)))
    col8 = _pick_col(col8_pos, w, rng)
    row2 = _pick_row(row2_pos, h, rng)
    g = full_grid(h, w, 0)
    rs = rng.sample([r for r in range(h) if r != row2],
                    min(n_eights, max(1, h - 1)))
    for r in rs:
        g[r][col8] = 8
    cs = rng.sample([c for c in range(w) if c != col8],
                    min(n_twos, max(1, w - 1)))
    for c in cs:
        g[row2][c] = 2
    return g


def _pick_col(bias, w, rng):
    if bias == "center":
        return w // 2
    if bias == "edge":
        return rng.choice([0, w - 1])
    return rng.randint(0, w - 1)


def _pick_row(bias, h, rng):
    if bias == "center":
        return h // 2
    if bias == "edge":
        return rng.choice([0, h - 1])
    return rng.randint(0, h - 1)



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Scattered evidence must uniquely identify one 8-column and one 2-row;
    color 4 is absent until the rule writes the intersection."""
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    eight_cols = [c for c in range(w) if sum(1 for r in range(h) if grid[r][c] == 8) >= 2]
    two_rows = [r for r in range(h) if sum(1 for c in range(w) if grid[r][c] == 2) >= 2]
    if len(eight_cols) != 1 or len(two_rows) != 1:
        errs.append(f"expected unique evidence column/row, got eight_cols={eight_cols}, two_rows={two_rows}")
        return errs
    col8, row2 = eight_cols[0], two_rows[0]
    eights = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 8]
    twos = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    if not (2 <= len(eights) <= 4):
        errs.append(f"expected 2-4 color-8 evidence cells, found {len(eights)}")
    if not (2 <= len(twos) <= 4):
        errs.append(f"expected 2-4 color-2 evidence cells, found {len(twos)}")
    if any(c != col8 for _, c in eights):
        errs.append(f"not all 8-cells lie in column {col8}: {eights}")
    if any(r != row2 for r, _ in twos):
        errs.append(f"not all 2-cells lie in row {row2}: {twos}")
    if any(r == row2 for r, _ in eights) or any(c == col8 for _, c in twos):
        errs.append("input already paints the row/column intersection; it should be blank before rule writes color 4")
    other = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 2, 8)]
    if other:
        errs.append(f"unexpected non-bg colors in input: {other[:5]}")
    return errs

def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    col8 = w // 2
    row2 = h // 2
    if name == "no_eights":
        for c in range(w):
            if c != col8:
                g[row2][c] = 2
        return g
    if name == "no_twos":
        for r in range(h):
            if r != row2:
                g[r][col8] = 8
        return g
    if name == "all_intersection":
        # col8 == row2's col → no clear cross
        for r in range(h):
            g[r][col8] = 8
        for c in range(w):
            g[row2][c] = 2
        return g
    return g
