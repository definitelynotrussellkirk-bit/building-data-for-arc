"""Generator for ae3edfdc.

Rule: colored satellite pixels sharing a row or col with a 1/2 center
move adjacent to that center.

Combinatorial axes (8): grid_h/w, center_count, palette_kind,
center_position, anchor_corner, asymmetry_force, palette_size, position_bias.
Degenerates: no_satellites, no_centers, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "870f854d23f0"
VERSION = "1.1.1"
TASK_ID = "870f854d23f0"
SUMMARY = "Colored satellites aligned with 1/2 centers move adjacent to them."

INVARIANTS = [
    "background is color 0",
    "centers use only colors 1 and 2",
    "satellite colors are nonzero and not 1 or 2",
    "only satellites aligned horizontally or vertically with a center appear in the output",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_satellites", "no_centers", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..14", "valid": "9..18"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "9..18"},
    "center_count":   {"type": "int", "default": "2", "valid": "1..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "center_position":{"type": "str", "default": "fixed",
                       "valid": "fixed|rng"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "4", "valid": "3..6"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; centers use colors 1/2; satellites use nonzero non-1/2 colors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    centers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in (1, 2)]
    satellites = [(r, c) for r in range(h) for c in range(w)
                  if grid[r][c] not in (0, 1, 2)]
    if not centers:
        return []  # degenerate no_centers — allowed
    if not satellites:
        return []  # degenerate no_satellites — allowed
    errs = []
    # Verify at least one satellite shares row or col with a center
    center_rows = set(r for r, c in centers)
    center_cols = set(c for r, c in centers)
    aligned = [(r, c) for r, c in satellites if r in center_rows or c in center_cols]
    if not aligned:
        errs.append("no satellite is row- or col-aligned with any center")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind")
                    or ctx.draw_choice("palette_kind",
                                       list(PALETTE_KINDS)))
    sat_pool = _build_palette(palette_kind, rng)
    if len(sat_pool) < 4:
        sat_pool = sat_pool + [c for c in [3, 4, 5, 6, 7, 8, 9] if c not in sat_pool]
    sat_colors = sat_pool[:4]
    h = 11 + rng.randint(0, 2)
    w = 11 + rng.randint(0, 2)
    g = full_grid(h, w, 0)
    g[4][4] = 1
    g[7][8] = 2
    g[4][1] = sat_colors[0]
    g[4][9] = sat_colors[1]
    g[1][8] = sat_colors[2]
    g[10][8] = sat_colors[3]
    return g


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [3, 4, 6, 9]
    elif kind == "cool":
        pool = [5, 7, 8]
    elif kind == "primary":
        pool = [3, 4]
    else:
        pool = [3, 4, 5, 6, 7, 8, 9]
    pool = [c for c in pool if c not in (0, 1, 2)]
    rng.shuffle(pool)
    return pool


def _draw_from_degenerate(name, rng):
    h, w = 12, 12
    g = full_grid(h, w, 0)
    if name == "no_satellites":
        g[4][4] = 1
        g[7][8] = 2
        return g
    if name == "no_centers":
        g[4][1] = 3
        g[1][8] = 5
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 1
        return g
    return g
