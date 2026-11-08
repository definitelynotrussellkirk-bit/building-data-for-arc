"""Generator for arc_puzzle_bank_21_set4_d:medium_d06.

A singleton marker shares its color with one larger object. The rule crops that
larger object and centers it on a blank canvas of the original size.

Combinatorial axes (8): grid_h, grid_w, palette_kind, shape,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_marker, no_match_object, multiple_match_objects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d1f49881a17d"
VERSION = "2.1.0"
TASK_ID = "d1f49881a17d"
SUMMARY = (
    "0-bg grid (h, w~10-13) "
    "with: (a) A SINGLETON "
    "MARKER — single cell "
    "at (1, w-2) (top-right "
    "interior) in a chosen "
    "shared color C from "
    "{2, 3, 4, 6, 7, 8, 9}; "
    "(b) A LARGER OBJECT of "
    "the SAME color C — a "
    "4-5 cell shape drawn "
    "from a shape bank, "
    "placed near the bottom-"
    "left at anchor (h-5, "
    "1); (c) A DISTRACTOR "
    "L-tromino of COLOR 5 "
    "at fixed top-left "
    "(rows 2-3, cols 2-3) "
    "in a different color. "
    "Rule (CROP LARGER "
    "OBJECT MATCHING THE "
    "MARKER COLOR, CENTER "
    "ON BLANK CANVAS OF "
    "ORIGINAL SIZE): find "
    "the SINGLETON MARKER "
    "(a single cell) — its "
    "color is C. Find the "
    "LARGER OBJECT (≥2 "
    "cells) sharing color "
    "C (4-connected "
    "component). EXTRACT "
    "its bbox crop, then "
    "PAINT it CENTERED on "
    "a fresh blank canvas "
    "of the ORIGINAL h × w "
    "dimensions (centered "
    "at ((h - bbox_h)//2, "
    "(w - bbox_w)//2)). "
    "Marker and distractor "
    "objects are discarded. "
    "Net: only the matching "
    "larger object survives, "
    "centered on a blank "
    "canvas."
)

INVARIANTS = [
    "exactly one color has both a singleton marker and a larger object",
    "the selected larger object is not already centered",
    "distractor objects, if present, use different colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_match_object", "multiple_match_objects")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..13", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "shape":          {"type": "int", "default": "rng 0..2", "valid": "0..2"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "marker_plus_match_plus_distractor",
                       "valid": "marker_plus_match_plus_distractor"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SHAPES = [
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],
    [(0, 1), (1, 0), (1, 1), (1, 2)],
]


def _paint(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify one singleton marker and exactly one larger same-color object."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    h, w = len(grid), len(grid[0])
    if h < 5 or w < 5:
        errs.append(f"grid too small for marker/object layout: {h}x{w}")
        return errs
    marker_val = grid[1][w - 2]
    if marker_val in (0, 5):
        errs.append(f"marker cell at (1,w-2) has {marker_val}; expected shared non-5 color")
        return errs

    def comps_for(color):
        cells = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
        seen = set(); comps = []
        for start in cells:
            if start in seen:
                continue
            stack = [start]; seen.add(start); comp = []
            while stack:
                r, c = stack.pop(); comp.append((r, c))
                for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    nb = (r + dr, c + dc)
                    if nb in cells and nb not in seen:
                        seen.add(nb); stack.append(nb)
            comps.append(comp)
        return comps

    marker_comps = comps_for(marker_val)
    singleton = [c for c in marker_comps if len(c) == 1 and c[0] == (1, w - 2)]
    larger = [c for c in marker_comps if len(c) >= 2]
    if len(singleton) != 1:
        errs.append(f"shared color {marker_val} does not have the required singleton marker")
    if len(larger) != 1:
        errs.append(f"shared color {marker_val} has {len(larger)} larger components; expected 1")
    elif not (4 <= len(larger[0]) <= 6):
        errs.append(f"selected larger object has {len(larger[0])} cells; expected 4..6")
    if len(comps_for(5)) != 1 or sum(grid[r][c] == 5 for r in range(h) for c in range(w)) != 3:
        errs.append("color-5 distractor should be one 3-cell component")
    other = sorted({grid[r][c] for r in range(h) for c in range(w)} - {0, 5, marker_val})
    if other:
        errs.append(f"unexpected extra distractor colors: {other}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 12, 13)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 10, 13)
    cells = _SHAPES[ctx.draw_int("shape", 0, len(_SHAPES) - 1)]
    color = rng.choice([2, 3, 4, 6, 7, 8, 9])
    g = full_grid(h, w, 0)
    g[1][w - 2] = color
    _paint(g, h - 5, 1, cells, color)
    g[2][2] = 5
    g[2][3] = 5
    g[3][2] = 5
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 11
    g = full_grid(h, w, 0)
    if name == "no_marker":
        # larger object exists but no singleton marker → no selection signal
        _paint(g, h - 5, 1, _SHAPES[0], 4)
        g[2][2] = 5; g[2][3] = 5; g[3][2] = 5
        return g
    if name == "no_match_object":
        # marker exists but no larger object of same color → "select match" fails
        g[1][w - 2] = 4
        g[2][2] = 5; g[2][3] = 5; g[3][2] = 5  # only distractor of color 5
        return g
    if name == "multiple_match_objects":
        # 2 larger objects share marker color → ambiguous selection
        g[1][w - 2] = 4
        _paint(g, h - 5, 1, _SHAPES[0], 4)
        _paint(g, 5, 6, _SHAPES[1], 4)  # also same color
        return g
    return g
