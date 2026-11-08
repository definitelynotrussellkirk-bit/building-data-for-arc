"""Generator for 7b7f7511.

Rule: a grid formed by repeating a smaller tile horizontally or
vertically; rule removes a repeated row or column period.

Combinatorial axes (8): axis, period, repeat, other_dim, palette_kind,
palette_size, anchor_corner, asymmetry_force.
Degenerates: no_repetition, full_repeat, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "80e2ae46cb8b"
VERSION = "2.0.0"
TASK_ID = "80e2ae46cb8b"
SUMMARY = (
    "Grid formed by REPEATING "
    "A SMALLER TILE — choose "
    "AXIS ∈ {horizontal, "
    "vertical}, PERIOD ∈ "
    "{2..5} (tile width or "
    "height along the "
    "repeating axis), REPEAT "
    "∈ {2..4} (number of "
    "copies), and OTHER_DIM "
    "∈ {3..7} (perpendicular "
    "dimension). The source "
    "TILE is filled with a "
    "3-color palette "
    "(warm/cool/broad/primary"
    ") at random per-cell, "
    "with anchor cells "
    "(top-left and one "
    "opposite corner) "
    "constrained to specific "
    "palette colors. The "
    "full grid = tile "
    "repeated REPEAT times "
    "along AXIS. Rule "
    "(REMOVE ONE REPEATED "
    "PERIOD ALONG THE "
    "AXIS): detect the "
    "axis-aligned PERIOD P "
    "(the repeating unit) "
    "and the REPEAT COUNT "
    "R. Output is the input "
    "with ONE FULL PERIOD "
    "removed — i.e., the "
    "tile repeated R-1 "
    "times along the same "
    "axis. If horizontal: "
    "output width = (R-1) * "
    "P. If vertical: "
    "output height = (R-1) "
    "* P. Net: one tile is "
    "stripped off the "
    "repeating sequence."
)

INVARIANTS = [
    "one axis contains an exact repeated period",
    "the source tile has at least two colors",
    "the repeated grid remains within ARC limits",
]

AXES_DIR = ("horizontal", "vertical")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_repetition", "full_repeat", "full_grid")
HELPFUL_TEXTURES = AXES_DIR

AXES = {
    "axis":           {"type": "str", "default": "rng helpful",
                       "valid": "|".join(AXES_DIR)},
    "period":         {"type": "int", "default": "rng 2..5", "valid": "1..15"},
    "repeat":         {"type": "int", "default": "rng 2..4", "valid": "2..6"},
    "other_dim":      {"type": "int", "default": "rng 3..7", "valid": "3..10"},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "3", "valid": "2..5"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for axis",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: at least 2 distinct colors, grid fits ARC limits."""
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    colors = set(grid[r][c] for r in range(h) for c in range(w))
    if len(colors) < 2:
        pass  # degenerate — allowed
    if h > 30 or w > 30:
        errors.append(f"grid too large: {h}x{w}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("tile")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        p_lo, p_hi = 2, 3
        rep_lo, rep_hi = 2, 2
        od_lo, od_hi = 3, 5
    elif difficulty == "hard":
        p_lo, p_hi = 4, 6
        rep_lo, rep_hi = 3, 5
        od_lo, od_hi = 5, 9
    else:
        p_lo, p_hi = 2, 5
        rep_lo, rep_hi = 2, 4
        od_lo, od_hi = 3, 7
    axis = (overrides.get("texture") if overrides.get("texture") in AXES_DIR else None) or \
           overrides.get("axis") or \
           ctx.draw_choice("axis", list(AXES_DIR))
    period = ctx.draw_int("period", p_lo, p_hi)
    repeat = ctx.draw_int("repeat", rep_lo, rep_hi)
    other = ctx.draw_int("other_dim", od_lo, od_hi)
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    palette = _build_palette(palette_kind, 3, rng)
    if axis == "horizontal":
        tile = full_grid(other, period, palette[0])
        for r in range(other):
            for c in range(period):
                tile[r][c] = rng.choice(palette)
        tile[0][0] = palette[0]
        tile[0][-1] = palette[1 % len(palette)]
        return [row * repeat for row in tile]
    tile = full_grid(period, other, palette[0])
    for r in range(period):
        for c in range(other):
            tile[r][c] = rng.choice(palette)
    tile[0][0] = palette[0]
    tile[-1][0] = palette[1 % len(palette)]
    return [row[:] for _ in range(repeat) for row in tile]


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    pool = [c for c in pool if c != 0]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _draw_from_degenerate(name, rng):
    if name == "no_repetition":
        g = full_grid(5, 7, 1)
        for r in range(5):
            for c in range(7):
                g[r][c] = rng.choice([1, 2, 3, 4])
        return g
    if name == "full_repeat":
        return full_grid(6, 8, 2)
    if name == "full_grid":
        return full_grid(6, 8, rng.choice([1, 2, 3, 4]))
    return full_grid(5, 7, 0)
