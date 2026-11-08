"""Generator for 5207a7b5.

Rule: vertical 5-bar at col defines col + bar-len. Left of bar fills 8s
in shrinking stairs, right fills 6s.

Combinatorial axes (8): grid_h/w, bar_len, bar_col_position,
position_bias, decoy_density, edge_clearance, palette_size,
asymmetry_force.
Degenerates: no_bar, full_height_bar, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "849c171da23c"
VERSION = "2.0.1"
TASK_ID = "849c171da23c"
SUMMARY = (
    "0-bg grid (h~8-14, w~"
    "7-14) with ONE VERTICAL "
    "BAR of COLOR 5 starting "
    "at row 0 — a single "
    "contiguous column at "
    "col c0 with length "
    "L ∈ [3, 7] (bar covers "
    "rows 0..L-1 at column "
    "c0). Bar column has "
    "edge_clearance ≥2 from "
    "both left and right "
    "borders. Position bias "
    "selects center / left "
    "/ right / spread. Rule "
    "(STAIR-STEP FILL FROM "
    "THE BAR — 8s LEFT, 6s "
    "RIGHT): the 5-bar has "
    "length L. For each row "
    "r in 0..L-1: fill cells "
    "(r, c0-1), (r, c0-2), ..."
    " out to (r, c0-(L-r)) "
    "with COLOR 8 (a left "
    "shrinking stair). And "
    "fill cells (r, c0+1), "
    "(r, c0+2), ..., out to "
    "(r, c0+(L-r)) with "
    "COLOR 6 (right "
    "shrinking stair). The "
    "5-bar stays. Net: each "
    "row of the bar emits a "
    "shrinking 8-pyramid to "
    "the left and 6-pyramid "
    "to the right."
)

INVARIANTS = [
    "background is 0",
    "single contiguous vertical bar of 5s starting at row 0",
    "bar_len in [3, 7]",
    "bar column has space >=2 to left and >=2 to right",
    "no other 5/8/6 cells in input",
]

POSITION_BIAS = ("center", "left_biased", "right_biased", "spread")
DEGENERATE_TEXTURES = ("no_bar", "full_height_bar", "single_cell")
HELPFUL_TEXTURES = POSITION_BIAS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "grid_w":            {"type": "int", "default": "rng 7..14", "valid": "5..18"},
    "bar_len":           {"type": "int", "default": "rng 3..6",
                          "valid": "2..8"},
    "bar_col_position":  {"type": "str", "default": "rng helpful",
                          "valid": "|".join(POSITION_BIAS)},
    "edge_clearance":    {"type": "int", "default": "2", "valid": "1..4"},
    "min_bar_len":       {"type": "int", "default": "3", "valid": "2..6"},
    "max_bar_len":       {"type": "int", "default": "7", "valid": "3..10"},
    "asymmetry_force":   {"type": "bool", "default": "false",
                          "valid": "true|false"},
    "texture":           {"type": "str", "default": "alias for bar_col_position",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: has color-5 cells forming a vertical bar starting at row 0 in a single column."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    fives = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if not fives:
        return []  # no_bar degenerate — allowed
    errs = []
    # all color-5 cells must be in the same column
    cols = {c for r, c in fives}
    if len(cols) > 1:
        errs.append(f"color-5 cells span {len(cols)} columns {sorted(cols)}; expected single column")
        return errs
    bar_col = list(cols)[0]
    # bar must start at row 0
    bar_rows = sorted(r for r, c in fives)
    if bar_rows[0] != 0:
        errs.append(f"color-5 bar starts at row {bar_rows[0]}; expected row 0")
    # bar must be contiguous
    for i in range(1, len(bar_rows)):
        if bar_rows[i] != bar_rows[i - 1] + 1:
            errs.append(f"color-5 bar has gap between row {bar_rows[i-1]} and {bar_rows[i]}")
            break
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 6, 9, 5, 8
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 12, 18, 12, 18
    else:
        h_lo, h_hi, w_lo, w_hi = 8, 14, 7, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    min_bl = int(overrides.get("min_bar_len", 3))
    max_bl = int(overrides.get("max_bar_len", min(7, h - 1)))
    bar_len = int(overrides.get("bar_len",
                                ctx.draw_int("bar_len", min_bl,
                                             min(max_bl, h - 1))))
    bar_len = max(2, min(h - 1, bar_len))
    pos_kind = (overrides.get("texture") or
                overrides.get("bar_col_position")
                or ctx.draw_choice("bar_col_position",
                                   list(POSITION_BIAS)))
    edge_clear = int(overrides.get("edge_clearance", 2))
    g = full_grid(h, w, 0)
    col_lo = edge_clear
    col_hi = w - edge_clear - 1
    if col_hi < col_lo:
        col_lo, col_hi = 0, w - 1
    if pos_kind == "center":
        col = (col_lo + col_hi) // 2
    elif pos_kind == "left_biased":
        col = col_lo + (col_hi - col_lo) // 4
    elif pos_kind == "right_biased":
        col = col_hi - (col_hi - col_lo) // 4
    else:
        col = rng.randint(col_lo, col_hi)
    for r in range(bar_len):
        if r < h:
            g[r][col] = 5
    return g


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_bar":
        return g
    if name == "full_height_bar":
        col = w // 2
        for r in range(h):
            g[r][col] = 5
        return g
    if name == "single_cell":
        g[0][w // 2] = 5
        return g
    return g
