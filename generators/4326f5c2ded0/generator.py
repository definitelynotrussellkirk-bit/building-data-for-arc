"""Semantic generator for ARC task 4326f5c2ded0.

Collect every nonzero cell, find the bottommost occupied row, and shift each
cell left by the vertical distance from that row.  Preserve row and color,
drop cells shifted beyond the left edge, clear all original positions, and
retain the input canvas dimensions.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "4326f5c2ded0"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "884d94dde3d6"
SUMMARY = "Shear every nonzero cell left by bottommost_row minus its row, preserving colors and canvas size."

INVARIANTS = [
    "background is 0 and at least one nonzero cell exists",
    "the bottommost occupied row defines zero shift",
    "each higher row shifts farther left by its vertical distance",
    "all nonzero colors and disconnected components obey the same shear",
    "negative target columns are clipped and all unfilled output cells are 0",
]

PUBLIC_PROFILES = (
    "public_train_1", "public_train_2", "public_train_3",
    "public_train_4", "public_train_5", "public_test_1",
)
GENERAL_PROFILES = (
    "connected_outline", "disconnected_objects", "multicolor_cells", "clipped_left",
    "severe_clipping", "two_row_signal", "tall_signal", "sparse_points",
    "bottom_anchor_cell", "row_gap",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {"scene_profile": {"type": "str", "default": "uniform rng over six linked public and ten generalized semantic lessons", "valid": "|".join(SCENE_PROFILES)}}


_PUBLIC_MASKS = {
    "public_train_1": (
        "0000000000000","0000000000000","0000000000000","0000aaaaa0000","0000a000a0000","0000aa00a0000",
        "00000a00aa000","00000a000a000","00000aaaaa000","0000000000000","0000000000000",
    ),
    "public_train_2": (
        "00000000000","00000000000","00000000000","0000aaa0000","0000a0a0000","0000a0a0000","0000a0a0000","0000aaa0000","00000000000","00000000000",
    ),
    "public_train_3": (
        "0000000000000","0000000000000","0000000000000","0000000aaa000","0000000a0a000","000000aa0aa00","000000a000a00","000000aaaaa00","0000000000000","0000000000000",
    ),
    "public_train_4": ("0000000","0aaa000","0aaa000","0000000","0000000","0000000","0000000"),
    "public_train_5": (
        "00000000000","00000000000","00aaaaa0000","00a000a0000","00a000a0000","00a000a0000","00aaaaa0000","00000000000","00000000000","00000000000",
    ),
    "public_test_1": (
        "0000000000000","0000000000000","0000000000000","000000aaa0000","0000aaa0a0000","0000a000a0000","0000aa00a0000",
        "00000a00aa000","00000a000a000","00000aaaaa000","0000000000000",
    ),
}
_PUBLIC_SIGNATURES = {mask: profile for profile, mask in _PUBLIC_MASKS.items()}
_DIRS = ((1,0),(-1,0),(0,1),(0,-1))


def _blank(height, width):
    return [[0 for _ in range(width)] for _ in range(height)]


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty grid"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["empty grid"], 0, 0
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"], height, width
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be integer ARC colors 0..9"], height, width
    return [], height, width


def _semantic_signature(grid):
    roles = {}
    names = iter("abcdefghi")
    rendered = []
    for row in grid:
        values = []
        for value in row:
            if value == 0:
                values.append("0")
            else:
                if value not in roles:
                    roles[value] = next(names)
                values.append(roles[value])
        rendered.append("".join(values))
    return tuple(rendered)


def _component_count(grid):
    height, width = len(grid), len(grid[0])
    seen, count = set(), 0
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            count += 1
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                current_row, current_col = stack.pop()
                for dr, dc in _DIRS:
                    nr, nc = current_row + dr, current_col + dc
                    if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] != 0 and (nr, nc) not in seen:
                        seen.add((nr, nc)); stack.append((nr, nc))
    return count


def _analysis(grid):
    errors, height, width = _validate_grid(grid)
    result = {"errors": errors, "height": height, "width": width, "scene_profile": None}
    if errors:
        return result
    cells = tuple((row, col, grid[row][col]) for row in range(height) for col in range(width) if grid[row][col] != 0)
    if not cells:
        errors.append("at least one nonzero cell is required because max-r on an empty list is undefined")
        result["cells"] = cells
        return result
    max_row = max(row for row, _, _ in cells)
    output = _blank(height, width)
    shifted, clipped = [], []
    for row, col, color in cells:
        new_col = col - (max_row - row)
        if 0 <= new_col < width:
            output[row][new_col] = color
            shifted.append((row, new_col, color))
        else:
            clipped.append((row, col, color))
    colors = tuple(sorted({color for _, _, color in cells}))
    occupied_rows = tuple(sorted({row for row, _, _ in cells}))
    row_gap = any(right - left > 1 for left, right in zip(occupied_rows, occupied_rows[1:]))
    components = _component_count(grid)
    bottom_count = sum(row == max_row for row, _, _ in cells)
    profile = _PUBLIC_SIGNATURES.get(_semantic_signature(grid))
    if profile is None:
        if len(clipped) * 5 >= len(cells) * 2:
            profile = "severe_clipping"
        elif clipped:
            profile = "clipped_left"
        elif len(colors) > 1:
            profile = "multicolor_cells"
        elif components == len(cells):
            profile = "sparse_points"
        elif bottom_count == 1 and components > 1:
            profile = "bottom_anchor_cell"
        elif row_gap:
            profile = "row_gap"
        elif len(occupied_rows) == 2:
            profile = "two_row_signal"
        elif occupied_rows[-1] - occupied_rows[0] >= 8:
            profile = "tall_signal"
        elif components > 1:
            profile = "disconnected_objects"
        elif components == 1:
            profile = "connected_outline"
    if profile not in SCENE_PROFILES:
        errors.append(f"unrecognized shear lesson {profile!r}")
    if output == [list(row) for row in grid]:
        errors.append("lesson must contain a visible non-identity shear")
    result.update({
        "errors": errors, "cells": cells, "max_row": max_row, "shifted_cells": tuple(shifted),
        "clipped_cells": tuple(clipped), "colors": colors, "occupied_rows": occupied_rows,
        "row_gap": row_gap, "component_count": components, "bottom_count": bottom_count,
        "output": output, "scene_profile": profile,
    })
    return result


def canonical_profile_signature(grid):
    info = _analysis(grid); profile = info.get("scene_profile")
    return profile if not info["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    info = _analysis(grid)
    if info["errors"]: raise ValueError("; ".join(info["errors"]))
    return {"scene_profile": info["scene_profile"]}


def rule_mirror(grid):
    info = _analysis(grid)
    if info["errors"]: raise ValueError("; ".join(info["errors"]))
    return [row[:] for row in info["output"]]


def _grid_from_public(profile, color):
    return [[0 if role == "0" else color for role in row] for row in _PUBLIC_MASKS[profile]]


def _dimensions(rng, difficulty):
    if difficulty == "easy": return rng.randint(9,13), rng.randint(10,15)
    if difficulty == "hard": return rng.randint(19,24), rng.randint(20,26)
    return rng.randint(14,19), rng.randint(15,21)


def _paint(grid, cells, colors):
    for index, (row, col) in enumerate(cells): grid[row][col] = colors[index % len(colors)]


def _general_grid(rng, difficulty, profile, colors):
    height, width = _dimensions(rng, difficulty)
    if profile in ("tall_signal", "bottom_anchor_cell"): height, width = max(height,14), max(width,16)
    if profile in ("disconnected_objects", "row_gap"): width = max(width,14)
    grid = _blank(height, width)
    if profile == "connected_outline":
        top, left = height//2-2, min(6, width-5)
        cells = [(top,c) for c in range(left,left+5)]+[(top+3,c) for c in range(left,left+5)]+[(r,left) for r in range(top+1,top+3)]+[(r,left+4) for r in range(top+1,top+3)]
        _paint(grid,cells,colors[:1])
    elif profile == "disconnected_objects":
        cells=[(4,c) for c in range(5,8)]+[(5,c) for c in range(5,8)]+[(6,c) for c in range(10,13)]+[(7,c) for c in range(10,13)]
        _paint(grid,cells,colors[:1])
    elif profile == "multicolor_cells":
        cells=[(4,7),(4,8),(5,7),(5,8),(6,7),(6,8)]
        _paint(grid,cells,colors[:3])
    elif profile == "clipped_left":
        cells=[(3,1),(4,4),(5,4),(6,4),(6,5)]
        _paint(grid,cells,colors[:1])
    elif profile == "severe_clipping":
        cells=[(2,0),(2,1),(3,0),(3,1),(4,1),(5,2),(6,2),(7,3)]
        _paint(grid,cells,colors[:1])
    elif profile == "two_row_signal":
        cells=[(height//2,4),(height//2,5),(height//2,6),(height//2+1,4),(height//2+1,5),(height//2+1,6)]
        _paint(grid,cells,colors[:1])
    elif profile == "tall_signal":
        top,left=2,10;cells=[(r,left) for r in range(top,top+10)]+[(top,left+1),(top+9,left+1)]
        _paint(grid,cells,colors[:1])
    elif profile == "sparse_points":
        cells=[(2,6),(4,7),(6,8),(8,9)]
        _paint(grid,cells,colors[:1])
    elif profile == "bottom_anchor_cell":
        cells=[(3,9),(3,10),(4,9),(4,10),(5,9),(5,10),(11,14)]
        _paint(grid,cells,colors[:1])
    elif profile == "row_gap":
        cells=[(3,c) for c in range(7,11)]+[(6,c) for c in range(10,14)]
        _paint(grid,cells,colors[:1])
    else: raise ValueError(f"unknown scene_profile: {profile!r}")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown=set(overrides)-{"scene_profile"}
    if unknown: raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested=overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES: raise ValueError(f"unknown scene_profile: {requested!r}")
    context=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=difficulty,overrides=overrides)
    profile=context.draw_choice("scene_profile",list(SCENE_PROFILES))
    colors=tuple(context.draw_distinct_colors("cell_colors",n=4,exclude={0}))
    rng=context.draw_rng("scene")
    if profile in PUBLIC_PROFILES:
        palette=(1,2,3,4,5,6,7,8,9); color=palette[(seed+2*PUBLIC_PROFILES.index(profile))%len(palette)]
        grid=_grid_from_public(profile,color)
    else:grid=_general_grid(rng,difficulty,profile,colors)
    observed=observe_overrides(grid)
    if observed!={"scene_profile":profile}:raise RuntimeError(f"profile construction mismatch: {profile} -> {observed}")
    return [row[:] for row in grid]


def self_check(grid, *, difficulty=None, meta=None):
    info=_analysis(grid);errors=list(info["errors"]);overrides=(meta or {}).get("overrides",{}) if isinstance(meta,dict) else {}
    if overrides:
        unknown=set(overrides)-{"scene_profile"}
        if unknown:errors.append(f"unknown override(s): {sorted(unknown)}")
        requested=overrides.get("scene_profile")
        if requested not in SCENE_PROFILES:errors.append(f"unknown scene_profile: {requested!r}")
        elif not errors and info["scene_profile"]!=requested:errors.append(f"requested scene_profile {requested}, observed {info['scene_profile']}")
    return errors
