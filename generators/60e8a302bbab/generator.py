"""Generator for 1d61978c.

Rule: count SE-diagonal pairs vs SW-diagonal pairs of 5s. Direction
with more pairs gets recolor 8, the other 2.

Combinatorial axes (8): grid_h/w, n_lines, line_length_max, position_bias,
palette_kind, anchor_corner, asymmetry_force, palette_size.
Degenerates: no_diagonals, full_grid, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "60e8a302bbab"
VERSION = "2.1.0"  # v2.1.0: line placement rejects unintended SW-diagonal 5-pairs so the direction-count witness is unambiguous.
TASK_ID = "60e8a302bbab"
SUMMARY = (
    "COLOR-7 (orange) background grid "
    "(h ∈ 12-16, w ∈ 14-18) with: 1-3 "
    "SE-DIAGONAL LINES of COLOR 5 "
    "(gray) — each line is "
    "(r0, c0), (r0+1, c0+1), ..., "
    "(r0+L-1, c0+L-1) of length L ∈ "
    "4..min(h, w)-2, placed at random "
    "top-left position with all cells "
    "starting on the 7-bg. Lines are "
    "non-overlapping (placement retries "
    "until clean). NO SW-DIAGONAL "
    "PAIRS of 5s exist by construction "
    "(only SE-diagonal lines are "
    "placed). Rule (COUNT SE-DIAGONAL "
    "VS SW-DIAGONAL ADJACENT 5-PAIRS; "
    "RECOLOR THE WINNING DIRECTION'S "
    "LINES TO COLOR 8, OTHER TO "
    "COLOR 2): SCAN every pair of "
    "diagonally-adjacent 5-cells. "
    "COUNT n_SE = pairs where "
    "(r1, c1) and (r1+1, c1+1) are "
    "both 5. COUNT n_SW = pairs where "
    "(r1, c1) and (r1+1, c1-1) are "
    "both 5. IF n_SE > n_SW: RECOLOR "
    "every 5 cell on an SE-diagonal "
    "line to COLOR 8 (cyan), and "
    "every 5 cell on a non-SE "
    "diagonal (SW) to COLOR 2 (red). "
    "ELSE: swap (SW→8, SE→2). Net: "
    "winning-direction lines become "
    "cyan, losing-direction lines "
    "become red, on the orange "
    "background."
)

INVARIANTS = [
    "bg = 7",
    "1-2 lines of 5s along SE (top-left to bottom-right) diagonals",
    "each line has >=3 cells",
    "no SW-diagonal 5-pairs",
]

POSITION_BIASES = ("scattered", "spread", "diagonal", "rng")
DEGENERATE_TEXTURES = ("no_diagonals", "full_grid", "single_cell")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..16", "valid": "10..20"},
    "grid_w":         {"type": "int", "default": "rng 14..18", "valid": "10..22"},
    "n_lines":        {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "line_length_max":{"type": "int", "default": "rng 4..min(h,w)-2",
                       "valid": "3..18"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 10, 12
        nl_lo, nl_hi = 1, 1
    elif difficulty == "hard":
        h_lo, h_hi = 16, 20
        nl_lo, nl_hi = 2, 3
    else:
        h_lo, h_hi = 12, 16
        nl_lo, nl_hi = 1, 2
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo + 2, h_hi + 2)
    g = [[7] * w for _ in range(h)]
    n_lines = int(overrides.get("n_lines",
                                ctx.draw_int("n_lines", nl_lo, nl_hi)))
    n_lines = max(1, min(3, n_lines))
    five_cells: set[tuple[int, int]] = set()
    for _ in range(n_lines):
        for _ in range(100):
            length = rng.randint(4, min(h - 2, w - 2))
            r0 = rng.randint(0, h - length); c0 = rng.randint(0, w - length)
            cells = [(r0 + i, c0 + i) for i in range(length)]
            cand = five_cells | set(cells)
            # Distinct SE lines can accidentally create SW-adjacent 5-pairs
            # between the lines, contradicting the "SE wins" teaching signal.
            has_sw_pair = any((r + 1, c - 1) in cand for r, c in cand)
            if not has_sw_pair and all(g[r][c] == 7 for r, c in cells):
                for r, c in cells:
                    g[r][c] = 5
                five_cells.update(cells)
                break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 13, 15
    g = [[7] * w for _ in range(h)]
    if name == "no_diagonals":
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    if name == "single_cell":
        g[6][7] = 5
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if any(v not in (5, 7) for row in grid for v in row):
        errs.append("normal examples should contain only bg=7 and line color=5")
    cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 5}
    se = sum(1 for r, c in cells if (r + 1, c + 1) in cells)
    sw = sum(1 for r, c in cells if (r + 1, c - 1) in cells)
    if se == 0:
        errs.append("need at least one SE-diagonal 5-pair")
    if sw != 0:
        errs.append("normal examples must not contain SW-diagonal 5-pairs")
    return errs
