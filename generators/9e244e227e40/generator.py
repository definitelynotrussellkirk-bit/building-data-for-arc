"""Generator for arc_puzzle_bank_seventh21:H48 — three-panel majority vote.

Rule: split into three 5x5 panels (single color-9 separators); the output
appends a 4th panel = per-cell majority (8 where >=2 of the 3 panels are ON).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9e244e227e40"
VERSION = "3.1.1"  # distribution fix: canonical input is 5x23 (3 SOURCE panels + 1 BLANK answer panel), not 5x17. v3.0 emitted only 3 panels (off-distribution; rule still appended a 4th). Now emit the blank 4th answer panel like canonical. (5x5 panels are rule-intrinsic -> shape stays 5x23.)
TASK_ID = "9e244e227e40"

SUMMARY = (
    "5-row, 23-col grid with THREE 5x5 binary SOURCE PANELS in non-0 colors "
    "plus a BLANK 4th (answer) panel, separated by single color-9 (maroon) "
    "columns at cols 5, 11, 17. Rule: split into the 5-wide panels; for each "
    "of the 25 cells the result is 8 (cyan) where at least 2 of the 3 source "
    "panels are ON (per-cell MAJORITY vote), else 0. The output rejoins the 3 "
    "source panels plus this 5x5 majority panel in the 4th slot. Colors are "
    "distractors -- only the ON/OFF masks and the per-cell majority matter."
)

INVARIANTS = [
    "background is 0; grid is 5 rows tall, 23 cols wide",
    "three 5x5 source panels + a blank 4th panel, separated by color-9 columns at cols 5, 11, 17",
    "each source panel is a binary mask in a non-0 color (color is a distractor)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_empty", "all_full", "single_panel")
HELPFUL_TEXTURES = PALETTE_KINDS

_PH, _PW, _NP = 5, 5, 3   # panel height, panel width, number of source panels

AXES = {
    "panel_on":       {"type": "int", "default": "rng per band", "valid": "1..25"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..7"},
    "position_bias":  {"type": "str", "default": "three_5x5_panels_9sep",
                       "valid": "three_5x5_panels_9sep"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..7"},
    "density":        {"type": "str", "default": "varies", "valid": "varies"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|all_empty|all_full|single_panel"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """5 rows × 23 cols; color-9 separators at cols 5, 11, 17; 3 non-blank source panels; blank 4th panel."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h != 5:
        errs.append(f"expected 5 rows, got {h}")
    if w != 23:
        errs.append(f"expected 23 cols, got {w}")
    if errs:
        return errs
    sep_cols = [5, 11, 17]
    for sc in sep_cols:
        if not all(grid[r][sc] == 9 for r in range(5)):
            errs.append(f"col {sc} is not all color-9 separator")
    # 4th panel (cols 18-22) should be blank
    if any(grid[r][c] != 0 for r in range(5) for c in range(18, 23)):
        errs.append("4th panel (cols 18-22) is not blank")
    # at least one source panel (first 3 panels) must have non-zero content
    for k in range(3):
        c0 = k * 6
        if not any(grid[r][c] != 0 for r in range(5) for c in range(c0, c0 + 5)):
            errs.append(f"source panel {k+1} (cols {c0}-{c0+4}) is blank")
    return errs


def _rand_panel_cells(rng, lo, hi):
    """A 5x5 binary pattern with between lo and hi ON cells (positions)."""
    cells = [(r, c) for r in range(_PH) for c in range(_PW)]
    return rng.sample(cells, rng.randint(lo, hi))


def _paint_panel(g, c0, on_cells, color):
    for (r, c) in on_cells:
        g[r][c0 + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    # density band: how many of the 25 cells are ON per panel
    if difficulty == "easy":
        lo, hi = 4, 10
    elif difficulty == "hard":
        lo, hi = 8, 18
    else:
        lo, hi = 6, 14

    n_slots = _NP + 1                    # 3 source panels + 1 blank answer panel
    w = n_slots * _PW + (n_slots - 1)    # 4*5 + 3 = 23 (matches canonical)
    g = full_grid(_PH, w, 0)
    for k in range(1, n_slots):          # color-9 separator columns at 5, 11, 17
        sep = k * (_PW + 1) - 1
        for r in range(_PH):
            g[r][sep] = 9
    palette = [1, 2, 3, 4, 5, 6, 7]
    for k in range(_NP):                 # only the 3 SOURCE panels get content
        c0 = k * (_PW + 1)
        _paint_panel(g, c0, _rand_panel_cells(rng, lo, hi), rng.choice(palette))
    # 4th panel (cols 18-22) stays blank — the answer slot the rule fills.
    return g


def _draw_from_degenerate(name, rng):
    n_slots = _NP + 1
    w = n_slots * _PW + (n_slots - 1)
    g = full_grid(_PH, w, 0)
    for k in range(1, n_slots):
        sep = k * (_PW + 1) - 1
        for r in range(_PH):
            g[r][sep] = 9
    if name == "all_empty":
        return g                          # three blank panels -> all-0 majority
    full = [(r, c) for r in range(_PH) for c in range(_PW)]
    for k in range(_NP):
        c0 = k * (_PW + 1)
        on = full if name == "all_full" else (full if k == 0 else [])
        _paint_panel(g, c0, on, 4)
    return g
