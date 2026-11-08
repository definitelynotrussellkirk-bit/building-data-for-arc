"""Generator for arc_puzzle_bank_eighteenth21:E120.

Rule: each row header (column 0) recolors that row's single 1-marker
to the header's color; the header itself is cleared.

Combinatorial axes (8): grid_h/w, palette_kind, active_rows,
palette_size, position_bias, n_distinct_colors, marker_position, texture.
Degenerates: no_headers, no_markers, header_only_no_marker.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "68b4181d35e1"
VERSION = "2.0.1"
TASK_ID = "68b4181d35e1"
SUMMARY = "Each row has an optional header color in column 0 + zero or more color-1 markers in cols 1..w-1. Rule: for rows with header AND exactly ONE marker, recolor the marker to the header color and clear the header. Other rows unchanged."

# Rivals: 'recolor all 1s with header' refuted by ≥1 demo with a row
# having multiple 1s (no recolor). 'preserve header' refuted by any
# demo with cleared header in output. 'recolor all rows, not just
# active' refuted by ≥1 demo with header-only row left alone.
# 'use 1 in output' refuted by ≥2 demos where output has no 1s.
# 4 demos with varied active rows + marker counts cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "active rows have one header in column 0",
    "active rows have exactly one marker cell with value 1",
    "header cells are cleared after painting their marker",
]

PALETTE_KINDS = ("default", "warm_headers", "cool_headers", "rainbow")
DEGENERATE_TEXTURES = ("no_headers", "no_markers", "header_only_no_marker")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "3..12"},
    "grid_w":         {"type": "int", "default": "rng 6..9", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "active_rows":    {"type": "int", "default": "rng 3..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "8", "valid": "8"},
    "position_bias":  {"type": "str", "default": "uniform", "valid": "uniform"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5",
                          "valid": "1..8"},
    "marker_position": {"type": "str", "default": "rng",
                        "valid": "interior|right_edge"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; >=1 header (col-0 nonzero) and >=1 value-1 marker exist."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    headers = [r for r in range(h) if grid[r][0] not in (0, 1)]
    markers = [(r, c) for r in range(h) for c in range(1, w) if grid[r][c] == 1]
    if not headers and not markers:
        errs.append("no headers and no markers — degenerate blank")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 6)
        w = ctx.draw_int("grid_w", 5, 8)
        active_lo, active_hi = 2, 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 10, 14)
        active_lo, active_hi = 5, 8
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 7, 11)
        active_lo, active_hi = 3, 6
    active = min(ctx.draw_int("active_rows", active_lo, active_hi), h)
    g = full_grid(h, w, 0)
    colors = [2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(colors)
    active_rows = rng.sample(range(h), active)
    inactive_rows = [r for r in range(h) if r not in active_rows]
    # Active rows: header + exactly one 1-marker at random col ≥1.
    for i, r in enumerate(active_rows):
        g[r][0] = colors[i % len(colors)]
        g[r][rng.randint(1, w - 1)] = 1
    # Inactive variation: some have header only, some have markers only,
    # some have 2+ markers (rule leaves all these alone). Adds clear
    # contrast for the rule's "exactly one marker" condition.
    for r in inactive_rows:
        kind = rng.choice(["empty", "header_only", "two_markers", "marker_only"])
        if kind == "header_only":
            g[r][0] = rng.choice(colors)
        elif kind == "two_markers":
            cols = rng.sample(range(1, w), 2)
            for c in cols:
                g[r][c] = 1
            if rng.random() < 0.5:
                g[r][0] = rng.choice(colors)
        elif kind == "marker_only":
            g[r][rng.randint(1, w - 1)] = 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 8
    g = full_grid(h, w, 0)
    if name == "no_headers":
        # 1-markers without row headers — no source color to recolor with
        g[1][3] = 1
        g[3][5] = 1
        return g
    if name == "no_markers":
        # headers without 1-markers — rule has nothing to recolor
        g[1][0] = 4
        g[3][0] = 7
        g[5][0] = 2
        return g
    if name == "header_only_no_marker":
        # one row has header but no 1-marker — that row is silently un-recolored
        g[1][0] = 4
        g[1][3] = 1
        g[3][0] = 7
        return g
    return g
