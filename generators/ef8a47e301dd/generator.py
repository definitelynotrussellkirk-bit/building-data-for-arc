"""Generator for puzzle 3bd67248.

Rule: the output is determined entirely by the grid dimensions and the corner
color g[0][0] (the rest of the input is ignored):
  - column 0           -> g[0][0] (bg color)
  - anti-diagonal (r+c == h-1, c != 0) -> 2
  - last row (r == h-1, not col 0 / anti-diag) -> 4
  - everything else    -> 0

Canonical inputs are a clean colored COLUMN 0 (= bg) on an otherwise-0 field.
The earlier generator flooded the WHOLE grid with bg plus random/blob/frame
"decoration" in extra colors — all rule-ignored AND absent from canonical
(poison). This version reproduces the canonical input distribution and varies
only the legitimate rule-safe axes: bg color and grid dimensions (incl.
non-square, which the rule's h-based anti-diagonal handles).

Degenerates: monochrome_bg, all_zero_input, decoy_anti_diag.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ef8a47e301dd"
VERSION = "3.0.0"  # canonical-faithful col0=bg input (was whole-grid bg + rule-ignored decoy decoration)
TASK_ID = "ef8a47e301dd"
SUMMARY = (
    "Grid (h, w in [3,18], square or non-square) whose COLUMN 0 is painted a BG "
    "color (any of {0..9} except 2 and 4, and nonzero so it is visible), with "
    "the rest of the grid 0 — matching the canonical clean-column input. Rule: "
    "output column 0 = bg (g[0][0]), the anti-diagonal (r+c==h-1) = 2, the last "
    "row = 4, else 0. The output depends only on dims and the corner color; bg "
    "color and dimensions vary."
)

INVARIANTS = [
    "bg color (g[0][0]) != 2 and != 4",
    "input is column-0 = bg, all other cells 0 (canonical distribution)",
    "h >= 3, w >= 3",
]

DEGENERATE_TEXTURES = ("monochrome_bg", "all_zero_input", "decoy_anti_diag")

AXES = {
    "grid_h":   {"type": "int", "default": "rng 4..14", "valid": "3..18"},
    "grid_w":   {"type": "int", "default": "rng 4..14", "valid": "3..18"},
    "bg_color": {"type": "color", "default": "rng (nonzero, !=2,4)", "valid": "1,3,5,6,7,8,9"},
    "texture":  {"type": "str", "default": "(degenerates only)",
                 "valid": "|".join(DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 3, 7
    elif difficulty == "hard":
        h_lo, h_hi = 11, 18
    else:
        h_lo, h_hi = 5, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, ctx, rng)
    bg = int(overrides.get("bg_color", ctx.draw_color("bg_color", exclude={0, 2, 4})))
    g = full_grid(h, w, 0)
    for r in range(h):           # canonical input: column 0 = bg, rest 0
        g[r][0] = bg
    return g


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or not isinstance(grid, list) or not all(isinstance(row, list) for row in grid):
        return ["grid is not a non-empty 2D list"]
    h = len(grid)
    w = len(grid[0]) if h else 0
    if any(len(row) != w for row in grid):
        return ["grid is ragged"]
    if h < 3 or w < 3:
        errors.append(f"grid too small, got {h}x{w}")
        return errors
    bg = grid[0][0]
    if bg in (0, 2, 4):
        errors.append(f"column-0 background color should be nonzero and not 2/4, got {bg}")
    for r in range(h):
        if grid[r][0] != bg:
            errors.append("column 0 is not a constant background color")
            break
    if any(grid[r][c] != 0 for r in range(h) for c in range(1, w)):
        errors.append("canonical input should have zeros outside column 0")
    return errors


def _draw_from_degenerate(name, h, w, ctx, rng):
    bg = ctx.draw_color("bg_color", exclude={0, 2, 4})
    if name == "monochrome_bg":
        return full_grid(h, w, bg)
    if name == "all_zero_input":
        return full_grid(h, w, 0)
    if name == "decoy_anti_diag":
        # Input mimics the output anti-diag pattern (rule still ignores it).
        g = full_grid(h, w, 0)
        for r in range(h):
            g[r][0] = bg
            for c in range(w):
                if r + c == h - 1 and c != 0:
                    g[r][c] = 2
        return g
    return full_grid(h, w, bg)
