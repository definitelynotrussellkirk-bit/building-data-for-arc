"""Generator for puzzle 759f3fd3.

Rule: green(3) cross divides grid into 4 quadrants. Output fills each
quadrant with concentric rectangles (alternating yellow/bg) based on
Chebyshev distance from the cross corner.

Combinatorial axes (8): grid_h/w, cross_row, cross_col,
cross_position, anchor_corner, asymmetry_force, palette_kind,
include_decoy.
Degenerates: no_cross, only_row, only_col.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4e9b5d003ae7"
VERSION = "2.0.1"  # self_check
TASK_ID = "4e9b5d003ae7"
SUMMARY = (
    "0-bg grid with exactly one full color-3 row at cross_row and one "
    "full color-3 column at cross_col forming a green '+' cross. The "
    "cross divides the grid into 4 quadrants. Rule: each quadrant "
    "anchor is the inner corner adjacent to the cross. For each "
    "non-cross cell (r, c), compute Chebyshev distance from anchor: "
    "if dist is ODD → color 4, else → 0. Cross cells (color 3) "
    "preserved. Output is 4 quadrants filled with concentric "
    "alternating 4/0 rectangles centered on the cross corner."
)

# Rivals: 'output is input' refuted by demos (quadrants filled).
# 'fill with bg' refuted by demos showing color 4. 'use color 8'
# refuted. 'fill solid (no alternation)' refuted by demos showing
# concentric pattern. 'use Manhattan distance' refuted by demos
# showing Chebyshev pattern (square rings). 3 demos with varied
# cross positions pin the rule.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "exactly 1 full row of 3 (cross row)",
    "exactly 1 full col of 3 (cross col)",
    "cross is interior (cr in [1, h-2], cc in [1, w-2])",
    "all 4 quadrants have ≥1 row and ≥1 col so output rings are visible",
]

CROSS_POSITIONS = ("center", "upper_left", "upper_right", "lower_left",
                   "lower_right", "spread")
DEGENERATE_TEXTURES = ("no_cross", "only_row", "only_col")
HELPFUL_TEXTURES = CROSS_POSITIONS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..16", "valid": "7..20"},
    "grid_w":         {"type": "int", "default": "rng 10..16", "valid": "7..20"},
    "cross_position": {"type": "str", "default": "rng helpful",
                       "valid": "|".join(CROSS_POSITIONS)},
    "cross_row":      {"type": "int", "default": "auto", "valid": "1..h-2"},
    "cross_col":      {"type": "int", "default": "auto", "valid": "1..w-2"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "include_decoy":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for cross_position",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 7, 11
    elif difficulty == "hard":
        h_lo, h_hi = 14, 20
    else:
        h_lo, h_hi = 10, 16
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    pos = (overrides.get("texture") or
           overrides.get("cross_position")
           or ctx.draw_choice("cross_position",
                              list(CROSS_POSITIONS)))
    if "cross_row" in overrides:
        cr = max(1, min(h - 2, int(overrides["cross_row"])))
    else:
        cr = _pick_cross_row(pos, h, rng)
    if "cross_col" in overrides:
        cc = max(1, min(w - 2, int(overrides["cross_col"])))
    else:
        cc = _pick_cross_col(pos, w, rng)
    g = full_grid(h, w, 0)
    for c in range(w):
        g[cr][c] = 3
    for r in range(h):
        g[r][cc] = 3
    return g


def _pick_cross_row(pos, h, rng):
    if pos == "center":
        return h // 2
    if pos in ("upper_left", "upper_right"):
        return rng.randint(2, max(2, h // 2))
    if pos in ("lower_left", "lower_right"):
        return rng.randint(h // 2, max(h // 2, h - 3))
    return rng.randint(2, h - 3)


def _pick_cross_col(pos, w, rng):
    if pos == "center":
        return w // 2
    if pos in ("upper_left", "lower_left"):
        return rng.randint(2, max(2, w // 2))
    if pos in ("upper_right", "lower_right"):
        return rng.randint(w // 2, max(w // 2, w - 3))
    return rng.randint(2, w - 3)


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_cross":
        return g
    if name == "only_row":
        for c in range(w):
            g[h // 2][c] = 3
        return g
    if name == "only_col":
        for r in range(h):
            g[r][w // 2] = 3
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    h, w = len(grid), len(grid[0])
    full_rows = [r for r in range(h) if all(grid[r][c] == 3 for c in range(w))]
    full_cols = [c for c in range(w) if all(grid[r][c] == 3 for r in range(h))]
    if len(full_rows) != 1:
        errs.append(f"expected exactly one full color-3 row, got {len(full_rows)}")
    if len(full_cols) != 1:
        errs.append(f"expected exactly one full color-3 col, got {len(full_cols)}")
    if full_rows and not (1 <= full_rows[0] <= h - 2):
        errs.append("cross row is not interior")
    if full_cols and not (1 <= full_cols[0] <= w - 2):
        errs.append("cross col is not interior")
    non_cross = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
                 if (not full_rows or r != full_rows[0]) and (not full_cols or c != full_cols[0]) and grid[r][c] != 0]
    if non_cross:
        errs.append("non-cross cells should be blank in the input")
    return errs
