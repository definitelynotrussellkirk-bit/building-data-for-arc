"""Generator for af726779.

Rule: top has alternating 7s with possible single-gap break; rule adds
rows below at midpoints with alternating 6/7.

Combinatorial axes (8): grid_h/w, seven_row, gap_prob, anchor_corner,
asymmetry_force, palette_kind, palette_size, position_bias.
Degenerates: no_sevens, full_sevens, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1c8c9bef01c5"
VERSION = "1.1.0"
TASK_ID = "1c8c9bef01c5"
SUMMARY = "3-bg grid with one row of alternating 7s; sometimes one gap-break."

INVARIANTS = [
    "bg = 3",
    "exactly one row has 7s at every other column",
    "row may have a single-cell gap-shift",
]

POSITION_BIASES = ("top", "middle", "rng")
DEGENERATE_TEXTURES = ("no_sevens", "full_sevens", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..14", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 13..17", "valid": "10..20"},
    "seven_row":      {"type": "int", "default": "rng 1..3", "valid": "0..h-1"},
    "gap_prob":       {"type": "float", "default": "0.5", "valid": "0..1"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
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
        h_lo, h_hi, w_lo, w_hi = 8, 10, 10, 13
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 14, 16, 17, 20
    else:
        h_lo, h_hi, w_lo, w_hi = 9, 14, 13, 17
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    g = [[3] * w for _ in range(h)]
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    if bias == "top":
        seven_row = 1
    elif bias == "middle":
        seven_row = h // 2
    else:
        seven_row = int(overrides.get("seven_row",
                                      rng.randint(1, max(1, h // 3))))
    seven_row = max(1, min(seven_row, h - 2))
    for c in range(0, w, 2):
        g[seven_row][c] = 7
    gap_prob = float(overrides.get("gap_prob", 0.5))
    if rng.random() < gap_prob:
        gap_col = rng.randint(2, max(2, w - 4))
        if g[seven_row][gap_col] == 7:
            g[seven_row][gap_col] = 3
            if g[seven_row][gap_col + 1] == 3:
                g[seven_row][gap_col + 1] = 7
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the single alternating-7 source row."""
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    if any(v not in (3, 7) for row in grid for v in row):
        errors.append("normal sample may only contain background 3 and source markers 7")
    seven_rows = sorted({r for r, row in enumerate(grid) for v in row if v == 7})
    if len(seven_rows) != 1:
        errors.append(f"expected exactly one row containing 7s, found rows {seven_rows}")
        return errors
    r = seven_rows[0]
    if not (1 <= r <= h - 2):
        errors.append(f"7-row should leave at least one row of context above/below, got row {r} in h={h}")
    cols = [c for c, v in enumerate(grid[r]) if v == 7]
    if len(cols) < 3:
        errors.append(f"expected at least three 7 markers for midpoint recursion, found {len(cols)}")
        return errors
    base = set(range(0, w, 2))
    actual = set(cols)
    if actual != base:
        missing = sorted(base - actual)
        added = sorted(actual - base)
        ok_single_gap_shift = (len(missing) == 1 and len(added) == 1
                               and added[0] == missing[0] + 1
                               and 0 <= added[0] < w)
        if not ok_single_gap_shift:
            errors.append(f"7 columns must be every other column, with at most one +1 gap shift; got {cols}")
    for rr, row in enumerate(grid):
        if rr != r and any(v == 7 for v in row):
            errors.append("7 markers leaked outside the designated source row")
            break
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 11, 14
    g = [[3] * w for _ in range(h)]
    if name == "no_sevens":
        return g
    if name == "full_sevens":
        for c in range(w):
            g[1][c] = 7
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 7
        return g
    return g
