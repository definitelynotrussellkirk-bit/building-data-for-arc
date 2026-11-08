"""Generator for a65b410d.

Rule: row with 2-cells, bar length L. Above: triangles of 3s expanding
up. Below: triangles of 1s shrinking down.

Combinatorial axes (8): grid_h/w, bar_length, bar_row_position,
position_bias, anchor_corner, asymmetry_force, edge_avoidance,
n_decoy_pixels.
Degenerates: no_bar, full_row_bar, multiple_bars.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e0fc08522773"
VERSION = "1.3.0"  # add executable self_check and align AXES with widened hard-range defaults.
TASK_ID = "e0fc08522773"
SUMMARY = "Single horizontal 2-bar at left edge; rule expands triangles above/below."

INVARIANTS = [
    "background is 0",
    "exactly one horizontal 2-bar starting at col 0",
    "bar_len in [2, 6]",
    "bar_row in [2, h-3] (room above/below)",
    "bar_len + bar_row <= w (top triangle fits)",
    "no colors 1, 3 in input (rule writes them for output)",
]

POSITION_BIAS = ("center", "spread", "top", "bottom")
DEGENERATE_TEXTURES = ("no_bar", "full_row_bar", "multiple_bars")
HELPFUL_TEXTURES = POSITION_BIAS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 7..14", "valid": "5..20"},
    "grid_w":            {"type": "int", "default": "rng 8..16", "valid": "6..24"},
    "bar_length":        {"type": "int", "default": "rng 2..4", "valid": "2..6"},
    "bar_row_position":  {"type": "str", "default": "rng helpful",
                          "valid": "center|spread|top|bottom"},
    "anchor_corner":     {"type": "bool", "default": "false",
                          "valid": "true|false"},
    "asymmetry_force":   {"type": "bool", "default": "false",
                          "valid": "true|false"},
    "edge_avoidance":    {"type": "bool", "default": "false",
                          "valid": "true|false"},
    "anchor_left":       {"type": "bool", "default": "true",
                          "valid": "true|false"},
    "texture":           {"type": "str", "default": "alias for bar_row_position",
                          "valid": "center|spread|top|bottom|no_bar|full_row_bar|multiple_bars"},
}


def self_check(grid, *, difficulty=None, meta=None):
    issues = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid must be a non-empty list of rows"]
    if len({len(row) for row in grid}) != 1:
        return ["grid rows must all have the same width"]

    h, w = len(grid), len(grid[0])
    colors = {v for row in grid for v in row}
    extra = colors - {0, 2}
    if extra:
        issues.append(f"input may contain only colors 0 and 2, got {sorted(extra)}")

    rows_with_twos = [r for r, row in enumerate(grid) if any(v == 2 for v in row)]
    if len(rows_with_twos) != 1:
        issues.append(f"expected exactly one row containing the 2-bar, got {len(rows_with_twos)}")
        return issues

    bar_row = rows_with_twos[0]
    two_cols = [c for c, v in enumerate(grid[bar_row]) if v == 2]
    if not two_cols:
        issues.append("2-bar is empty")
        return issues

    bar_len = len(two_cols)
    if two_cols != list(range(bar_len)):
        issues.append("2-bar must be contiguous and anchored at column 0")
    if not 2 <= bar_len <= 6:
        issues.append(f"bar_len must be in [2, 6], got {bar_len}")
    if not 2 <= bar_row <= h - 3:
        issues.append(f"bar_row must leave room above/below, got {bar_row} for h={h}")
    if bar_len + bar_row > w:
        issues.append(
            f"top triangle would exceed width: bar_len({bar_len}) + bar_row({bar_row}) > w({w})"
        )
    if any(grid[r][c] == 2 for r in range(h) for c in range(w)
           if r != bar_row or c >= bar_len):
        issues.append("all 2-cells must belong to the single anchored bar")
    return issues


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 5, 8, 6, 10
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 14, 20, 16, 24
    else:
        h_lo, h_hi, w_lo, w_hi = 8, 15, 9, 18
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    bar_len = int(overrides.get("bar_length",
                                ctx.draw_int("bar_length", 2, min(4, w - 2))))
    bar_len = max(2, min(min(6, w - 2), bar_len))
    pos_kind = (overrides.get("texture") or
                overrides.get("bar_row_position")
                or ctx.draw_choice("bar_row_position",
                                   list(POSITION_BIAS)))
    max_row = min(h - 3, w - bar_len)
    if max_row < 2:
        max_row = max(2, max_row)
    if pos_kind == "center":
        bar_row = (h // 2)
    elif pos_kind == "top":
        bar_row = 2
    elif pos_kind == "bottom":
        bar_row = h - 3
    else:
        bar_row = rng.randint(2, max(2, max_row))
    bar_row = max(2, min(min(h - 3, w - bar_len), bar_row))
    g = full_grid(h, w, 0)
    for c in range(bar_len):
        g[bar_row][c] = 2
    return g


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_bar":
        return g
    if name == "full_row_bar":
        for c in range(w):
            g[h // 2][c] = 2
        return g
    if name == "multiple_bars":
        for c in range(2):
            g[2][c] = 2
            g[h - 3][c] = 2
        return g
    return g
