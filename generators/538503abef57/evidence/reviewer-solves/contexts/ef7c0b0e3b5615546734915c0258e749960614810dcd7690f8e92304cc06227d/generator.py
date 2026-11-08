"""Square-frame component reflection sampler; Racket remains the label authority.

Default lessons alternate canonical-sized objects and rich witnesses. A four-pair
window contains two witnesses, so any three demonstrations refute the declared
color-grouping and fixed-three-frame rivals. Explicit overrides are instance
controls; they do not inherit that default lesson guarantee.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components, bbox

GENERATOR_ID = "538503abef57"
TASK_ID = GENERATOR_ID
RULE_HASH = "2fbbe9d88e5d"
VERSION = "2.0.0"
SUMMARY = "Reflect separate monochrome components in their own square frames; vary shapes, sizes, colors and repeated-color objects."
INVARIANTS = [
    "integer ARC colors 0..9; background 0; 2..4 monochrome 4-connected components",
    "each component has a square 2x2 or 3x3 bounding box",
    "whole bounding boxes have a blank row or column between them, before and after reflection",
    "2..5 distinct colors including background; colors may identify several separate components",
    "default four-pair windows contain two grouping/size witnesses; overrides control individual inputs only",
]
AXES = {
    "grid_h": {"type": "int", "default": "8..16 with canonical profile mixture", "valid": "8..16"},
    "grid_w": {"type": "int", "default": "8..16 with canonical profile mixture", "valid": "8..16"},
    "n_objects": {"type": "int", "default": "2 core or 3 witness", "valid": "2..4"},
    "n_distinct_colors": {"type": "int", "default": "3 including background", "valid": "2..5"},
}
# Exact impossible tuples, not a blanket exemption of the two dimensions.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"n_objects": 2, "n_distinct_colors": 4},
    {"n_objects": 2, "n_distinct_colors": 5},
    {"n_objects": 3, "n_distinct_colors": 5},
]
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("witness", "core")
MIN_STRICT_FRAC = 1.0


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % 2]


def _dihedral_shapes(cells, side):
    """Immutable geometry used for input shape diversity, not output labels."""
    current = frozenset(cells)
    views = []
    for _ in range(4):
        views.extend((current, frozenset((c, r) for r, c in current)))
        current = frozenset((c, side-1-r) for r, c in current)
    return views


@lru_cache(maxsize=4)
def _shape_pool(side, rigid=False):
    shapes = []
    for mask in range(1, 1 << (side * side)):
        cells = tuple((r, c) for r in range(side) for c in range(side)
                      if mask & (1 << (r * side + c)))
        if bbox(cells) != (0, 0, side-1, side-1):
            continue
        if set(cells) == {(side-1-c, side-1-r) for r, c in cells}:
            continue
        sample = [[int((r, c) in cells) for c in range(side)] for r in range(side)]
        if len(components(sample)) != 1:
            continue
        if rigid and len(set(_dihedral_shapes(cells, side))) != 8:
            continue
        shapes.append(cells)
    if not shapes:
        raise RuntimeError("empty connected-shape pool")
    return tuple(shapes)


def _separated(a, b):
    return a[2]+1 < b[0] or b[2]+1 < a[0] or a[3]+1 < b[1] or b[3]+1 < a[1]


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rectangular grid"]
    if not 1 <= len(grid) <= 30 or not 1 <= len(grid[0]) <= 30:
        return ["grid dimensions outside ARC 1..30"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer colors 0..9"]
    palette = {v for row in grid for v in row}
    if 0 not in palette or not 2 <= len(palette) <= 5:
        return ["require background 0 and 1..4 foreground colors"]
    parts = components(grid)
    errors = []
    if not 2 <= len(parts) <= 4:
        errors.append("require 2..4 monochrome connected components")
    for part in parts:
        r0, c0, r1, c1 = part["bbox"]
        if r1-r0 != c1-c0 or r1-r0 not in (1, 2):
            errors.append("each component must have a square 2x2 or 3x3 bbox")
    if any(not _separated(a["bbox"], b["bbox"]) for a, b in combinations(parts, 2)):
        errors.append("component bounding boxes need a full blank row or column between them")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_objects": len(components(grid)),
            "n_distinct_colors": len({v for row in grid for v in row})}


def _dimensions(ctx):
    # Sampling mode changes weights only; every exact boundary works in every band.
    anchor = ctx.draw_rng("canonical_profile").choice(((9, 11), (10, 12), (11, 13)))
    core = ctx.draw_choice("profile_mixture", (True, True, False))
    dims = []
    for name, target in zip(("grid_h", "grid_w"), anchor):
        choices = list(range(8, 17)) + ([target] * 150 if core else [])
        dims.append(ctx.draw_choice(name, choices))
    return dims


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty is not None and (type(difficulty) is not str or difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    witness = schedule_profile(seed, sample_index, difficulty) == "witness"
    h, w = _dimensions(ctx)
    wanted_colors = overrides.get("n_distinct_colors")
    default_n = max(3 if witness else 2, (wanted_colors or 3)-1)
    # Singleton default draws preserve exact schedule AND truthful provenance.
    # An explicit control sees its entire declared domain in every band.
    n = ctx.draw_choice("n_objects", (2, 3, 4) if overrides.get("n_objects") is not None else (default_n,))
    count = ctx.draw_choice("n_distinct_colors", (2, 3, 4, 5) if wanted_colors is not None else (3,))
    if count > n + 1:
        raise ValueError("n_distinct_colors includes background and cannot exceed n_objects + 1")
    palette = ctx.draw_distinct_colors("object_palette", n=count-1, exclude={0})
    # Unequal-size repeated components refute grouping when placed in opposite
    # NW/SE quadrants. Their sizes prevent exchanging one component for the other.
    repeat = n > len(palette)
    sizes = [2 if witness or repeat else 3] + [3] * (n-1)
    colors = [palette[0], palette[0]] if repeat else list(palette[:2])
    colors += list(palette[1:]) if repeat else list(palette[2:])
    colors = (colors + [palette[-1]] * n)[:n]
    layout = ctx.draw_rng("layout")
    row_cut, col_cut = layout.randint(3, h-4), layout.randint(3, w-4)
    regions = [(0, row_cut, 0, col_cut), (0, row_cut, col_cut+1, w),
               (row_cut+1, h, 0, col_cut), (row_cut+1, h, col_cut+1, w)]
    if repeat:
        order = [0, 3] if layout.choice((False, True)) else [3, 0]
        rest = [1, 2]
        layout.shuffle(rest)
        order += rest
    else:
        order = layout.sample(range(4), 4)
    grid = full_grid(h, w, 0)
    for i, (side, color, slot) in enumerate(zip(sizes, colors, order)):
        top, bottom, left, right = regions[slot]
        r0, c0 = layout.randint(top, bottom-side), layout.randint(left, right-side)
        pool = _shape_pool(side, rigid=(i == 1))
        if difficulty == "easy":
            preferred = tuple(p for p in pool if len(p) <= 5)
        elif difficulty == "hard":
            preferred = tuple(p for p in pool if len(p) >= 6)
        else:
            preferred = ()
        cells = layout.choice(pool + preferred)
        for r, c in cells:
            grid[r0+r][c0+c] = color
    return grid


def _rival_projection(grid, grouping="component", fixed_side=None, transform="anti"):
    """Alternative hypotheses only. Never called to provide dataset labels."""
    parts = components(grid)
    if grouping == "color":
        colors = sorted({p["color"] for p in parts})
        parts = [{"color": color,
                  "cells": [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]}
                 for color in colors]
    out = full_grid(len(grid), len(grid[0]), 0)
    for part in parts:
        r0, c0, r1, c1 = bbox(part["cells"])
        height, width = r1-r0+1, c1-c0+1
        if fixed_side is not None:
            height = width = fixed_side
        for r, c in part["cells"]:
            u, v = r-r0, c-c0
            if transform == "main":
                rr, cc = r0+v, c0+u
            elif transform == "half_turn":
                rr, cc = r0+height-1-u, c0+width-1-v
            else:
                rr, cc = r0+width-1-v, c0+height-1-u
            if 0 <= rr < len(out) and 0 <= cc < len(out[0]):
                out[rr][cc] = part["color"]
    return out


def _by_color(grid):
    return _rival_projection(grid, grouping="color")


def _fixed_three(grid):
    return _rival_projection(grid, fixed_side=3)


def _main_diagonal(grid):
    return _rival_projection(grid, transform="main")


def _half_turn(grid):
    return _rival_projection(grid, transform="half_turn")


def _grouping_witness(grid):
    parts = components(grid)
    # Positive-slope separation and unequal frame sizes make color grouping
    # move the components outside their own local frames (or exchange sizes).
    for a, b in combinations(parts, 2):
        ar, ac, ar1, ac1 = a["bbox"]
        br, bc, br1, bc1 = b["bbox"]
        if (a["color"] == b["color"] and sum(p["color"] == a["color"] for p in parts) == 2
                and ar1-ar != br1-br
                and ((ar1 < br and ac1 < bc) or (br1 < ar and bc1 < ac))):
            return True
    return False


def _size_witness(grid):
    return any(p["bbox"][2]-p["bbox"][0] == 1 for p in components(grid))


def _orientation_witness(grid):
    return any(len(set(_dihedral_shapes(p["norm"], p["bbox"][2]-p["bbox"][0]+1))) == 8
               for p in components(grid))


SEMANTIC_RIVALS = {"by_color": _by_color, "fixed_three": _fixed_three,
                   "main_diagonal": _main_diagonal, "half_turn": _half_turn}
CANONICAL_SHORTCUTS = {"by_color": _by_color, "fixed_three": _fixed_three}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {"separate_same_color": _grouping_witness,
                      "variable_frame_size": _size_witness,
                      "orientation": _orientation_witness}
WITNESS_RIVALS = {"separate_same_color": ["by_color"],
                  "variable_frame_size": ["fixed_three"],
                  "orientation": ["main_diagonal", "half_turn"]}
