"""Generator for arc_additional_puzzle_bank_volume11:H76.

Rule: a direction-coded source traces a cyan beam through slash and
backslash mirrors until a wall or edge.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_source, no_mirrors, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "98066c7e6fc5"
VERSION = "2.0.1"
TASK_ID = "98066c7e6fc5"
SUMMARY = (
    "0-bg grid (h~9-13, w~"
    "11-16) with: (a) ONE "
    "DIRECTION-CODED SOURCE "
    "at (h-2, 1) — a single "
    "cell with COLOR 2 "
    "(direction index in "
    "[1..4]: 1=right, "
    "2=down, 3=left, 4=up "
    "per puzzle); (b) ONE "
    "SLASH MIRROR (COLOR "
    "6) at (h-2, mirror_c) "
    "with mirror_c ∈ [4, "
    "w-4]; (c) ONE WALL "
    "(COLOR 5) at (2, "
    "mirror_c) blocking "
    "upward travel; (d) "
    "OPTIONALLY ONE "
    "BACKSLASH MIRROR "
    "(COLOR 7) at (h-2-3, "
    "mirror_c+2). Rule "
    "(TRACE CYAN BEAM "
    "FROM SOURCE THROUGH "
    "MIRRORS UNTIL EDGE/"
    "WALL): the source's "
    "value encodes a "
    "direction. Cast a "
    "beam from source's "
    "position in that "
    "direction. The beam "
    "traverses 0-cells "
    "(painting them COLOR "
    "8 cyan). When it "
    "hits a SLASH MIRROR "
    "(6), the beam "
    "reflects right-angle "
    "per the slash "
    "convention (e.g., "
    "right→up, down→left)"
    ". When it hits a "
    "BACKSLASH MIRROR (7), "
    "it reflects the "
    "other way (e.g., "
    "right→down, up→left). "
    "GRAY WALL (5) STOPS "
    "the beam. Edges of "
    "the grid also stop "
    "it. Source/mirrors/"
    "walls stay. Net: a "
    "cyan-painted "
    "trajectory traces "
    "through the optical "
    "system."
)

INVARIANTS = [
    "one start cell has a value from 1 through 4",
    "mirror cells are 6 or 7",
    "gray cells stop the beam",
    "the traced path includes at least one blank cell",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_source", "no_mirrors", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..13", "valid": "7..24"},
    "grid_w":         {"type": "int", "default": "rng 11..16", "valid": "9..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "true",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "4", "valid": "4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 cell of color 6 (mirror) and ≥1 cell of value 2 (source at bottom area)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h = len(grid)
    has_mirror = any(grid[r][c] == 6 for r in range(h) for c in range(len(grid[0])))
    has_source = any(grid[r][c] == 2 for r in range(h) for c in range(len(grid[0])))
    errs = []
    if not has_mirror:
        errs.append("no color-6 mirror cell")
    if not has_source:
        errs.append("no color-2 source cell")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 14, 16)
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 11, 16)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    row = h - 2
    g[row][1] = 2
    mirror_c = rng.randint(4, w - 4)
    g[row][mirror_c] = 6
    g[2][mirror_c] = 5
    if mirror_c + 2 < w:
        g[max(1, row - 3)][mirror_c + 2] = 7
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 13, 0)
    if name == "no_source":
        g[8][6] = 6
        g[2][6] = 5
        return g
    if name == "no_mirrors":
        g[8][1] = 2
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(13):
                g[r][c] = 6
        return g
    return g
