"""Generator for 234bbc79.

Rule: gray markers inherit nearest colors, then connected objects are
packed into a 3-row strip.

Combinatorial axes (8): grid_h/w, component_count, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_distinct_colors.
Degenerates: no_components, no_markers, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7284e86d3539"
VERSION = "2.2.0"  # v2.2.0: guarantee at least one gray marker in normal examples; v2.1.0 varied grid and component slots.
TASK_ID = "7284e86d3539"
SUMMARY = (
    "Fixed 6×16 0-bg grid with 2-4 COLORED 2-CELL "
    "VERTICAL COMPONENTS placed at FIXED COLUMN "
    "STARTS [1, 5, 9, 13] (one component per "
    "slot, separated by 4 columns). For EACH "
    "component i: pick a random row r ∈ {1..3}; "
    "paint cells (r, starts[i]) and (r+1, "
    "starts[i]) in a DISTINCT non-{0, 5} color "
    "drawn from {1..9}; with 50% probability "
    "ALSO paint cell (r+1, starts[i]+1) with "
    "COLOR 5 (a GRAY MARKER cell, signaling "
    "this component to be recolored). Other "
    "cells stay bg-0. Rule (GRAY MARKERS "
    "INHERIT NEAREST COLOR, COMPONENTS PACKED "
    "INTO 3-ROW STRIP): for EACH GRAY (color "
    "5) MARKER cell: find the NEAREST non-gray "
    "non-bg cell (its color C) — typically the "
    "adjacent component. RECOLOR the gray cell "
    "to C (so the gray inherits its nearest "
    "color, extending the component). Then "
    "extract every now-uniform-color component "
    "and PACK them into a 3-ROW OUTPUT STRIP "
    "(specifically, place each component's "
    "crop into a tight 3-row arrangement, "
    "preserving color, in order). Net: gray "
    "markers absorb into their neighbors and "
    "the colored components are gathered into "
    "a compact 3-row gallery."
)

INVARIANTS = [
    "nonzero non-gray colored components are separated by columns",
    "gray markers are nearest to their intended color component",
    "recolored components have height at most two",
    "component colors are distinct and exclude gray",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_components", "no_markers", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "6", "valid": "6"},
    "grid_w":         {"type": "int", "default": "16", "valid": "16"},
    "component_count":{"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
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
        cc_lo, cc_hi = 2, 3; h = ctx.draw_int("grid_h", 5, 7); w = ctx.draw_int("grid_w", 14, 18)
    elif difficulty == "hard":
        cc_lo, cc_hi = 4, 6; h = ctx.draw_int("grid_h", 6, 9); w = ctx.draw_int("grid_w", 20, 28)
    else:
        cc_lo, cc_hi = 2, 5; h = ctx.draw_int("grid_h", 5, 8); w = ctx.draw_int("grid_w", 16, 24)
    # one component per ~4-col slot; cap count to what fits
    max_comp = max(2, (w - 1) // 4)
    component_count = min(ctx.draw_int("component_count", cc_lo, cc_hi), max_comp)
    colors = ctx.draw_distinct_colors("colors", n=component_count, exclude={0, 5})
    g = full_grid(h, w, 0)
    slots = list(range(1, w - 1, 4))
    starts = rng.sample(slots, component_count)
    marker_slots = []
    made_marker = False
    for i in range(component_count):
        c = starts[i]
        r = rng.randint(1, h - 2)
        g[r][c] = colors[i]
        g[r + 1][c] = colors[i]
        if c + 1 < w:
            marker_slots.append((r + 1, c + 1))
            if rng.choice([True, False]):
                g[r + 1][c + 1] = 5
                made_marker = True
    if marker_slots and not made_marker:
        r, c = rng.choice(marker_slots)
        g[r][c] = 5
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(6, 16, 0)
    if name == "no_components":
        return g
    if name == "no_markers":
        for i, c in enumerate([1, 5, 9, 13]):
            g[2][c] = 2 + i
            g[3][c] = 2 + i
        return g
    if name == "full_grid":
        for r in range(6):
            for c in range(16):
                g[r][c] = 5
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate gray marker recoloring examples."""
    errs: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    gray = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    colored = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] not in (0, 5)]
    if not gray:
        errs.append("normal examples must include at least one gray marker")
    if len({v for _, _, v in colored}) < 2:
        errs.append("expected at least two colored components")
    for r, c in gray:
        if not any(0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] not in (0, 5) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            errs.append("every gray marker should be adjacent to its intended colored component")
            break
    return errs
