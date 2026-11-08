"""Reviewed generator for moving an arbitrary cropped object to a color-9 marker.

The exact canonical rule clears the source canvas, crops every non-{0,9} object
cell, and pastes that crop with its top-left at the unique marker.  Ordinary
lessons deliberately vary the object shape instead of hard-coding one L.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "d172afae0ee5"
VERSION = "2.0.0"
SUMMARY = "Move an arbitrary connected object crop to the unique color-9 marker."

PALETTES = {
    "default": (1, 2, 3, 4, 5, 6, 7, 8),
    "warm": (2, 4, 6),
    "cool": (1, 3, 8),
    "varied": (5, 7),
}
SHAPES = {
    # The first five are the normalized occupancies visible in the originals.
    "canonical_l4": ((0, 0), (1, 0), (2, 0), (2, 1)),
    "canonical_t4": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "canonical_zig4": ((0, 1), (0, 2), (1, 0), (1, 1)),
    "canonical_u5": ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    "canonical_corner3": ((0, 0), (0, 1), (1, 0)),
    "stair8": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3), (2, 3)),
}

INVARIANTS = [
    "background is 0 and cells are exact ARC integers",
    "there is exactly one color-9 marker outside the object bounding box",
    "all non-{0,9} cells form one four-connected object",
    "the marker can anchor the full object crop in bounds",
]
AXES = {
    "grid_h": {"type": "int", "default": "difficulty band", "valid": "6..30"},
    "grid_w": {"type": "int", "default": "difficulty band", "valid": "6..30"},
    "palette_kind": {"type": "str", "default": "rng", "valid": "|".join(PALETTES)},
    "object_color": {"type": "color", "default": "from palette_kind", "valid": "1..8"},
    "texture": {"type": "str", "default": "coverage schedule", "valid": "|".join(SHAPES)},
}
_ALLOWED_OVERRIDES = frozenset(AXES)


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise TypeError("seed must be an exact integer in 0..2**63-1")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative exact integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium or hard")
    unknown = set(overrides) - _ALLOWED_OVERRIDES
    if unknown:
        raise ValueError("unknown overrides: " + ", ".join(sorted(unknown)))


def _draw_int_axis(ctx, label, low, high, default_low, default_high, overrides):
    if label in overrides and overrides[label] is not None:
        value = overrides[label]
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{label} must be an exact integer in {low}..{high}")
        return ctx.draw_choice(label, tuple(range(low, high + 1)))
    return ctx.draw_int_strict(label, default_low, default_high)


def _draw_choice_axis(ctx, label, options, defaults, overrides):
    if label in overrides and overrides[label] is not None:
        value = overrides[label]
        if type(value) is not str or value not in options:
            raise ValueError(f"{label} must be one of {tuple(options)}")
        return ctx.draw_choice(label, tuple(options))
    return ctx.draw_choice(label, tuple(defaults))


def _components(cells):
    cells = set(cells)
    result = []
    while cells:
        start = min(cells)
        seen = {start}
        queue = deque([start])
        cells.remove(start)
        while queue:
            r, c = queue.popleft()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in cells:
                    cells.remove(point)
                    seen.add(point)
                    queue.append(point)
        result.append(seen)
    return result


def analyze(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty rectangular grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be exact integer ARC colors 0..9")
    h, w = len(grid), width
    if not 1 <= h <= 30 or not 1 <= w <= 30:
        raise ValueError("grid dimensions must be in 1..30")
    markers = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
             if value not in (0, 9)]
    if len(markers) != 1:
        raise ValueError("expected exactly one color-9 marker")
    if not cells:
        raise ValueError("expected at least one non-{0,9} object cell")
    if len(_components(cells)) != 1:
        raise ValueError("object must be four-connected")
    r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
    r1, c1 = max(r for r, _ in cells), max(c for _, c in cells)
    marker = markers[0]
    if r0 <= marker[0] <= r1 and c0 <= marker[1] <= c1:
        raise ValueError("marker must stay outside the source object bounding box")
    oh, ow = r1 - r0 + 1, c1 - c0 + 1
    if marker[0] + oh > h or marker[1] + ow > w:
        raise ValueError("marker cannot anchor the full crop in bounds")
    crop = [list(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]]
    return {"marker": marker, "cells": cells, "bbox": (r0, c0, r1, c1), "crop": crop}


def self_check(grid, *, difficulty=None, meta=None):
    try:
        analyze(grid)
        return []
    except (TypeError, ValueError) as exc:
        return [str(exc)]


def _paste(crop, marker, h, w):
    out = full_grid(h, w, 0)
    top, left = marker
    for r, row in enumerate(crop):
        for c, value in enumerate(row):
            if value != 0:
                out[top + r][left + c] = value
    return out


def rule_mirror(grid):
    info = analyze(grid)
    return _paste(info["crop"], info["marker"], len(grid), len(grid[0]))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    bands = {
        None: ((8, 16), (9, 17)),
        "easy": ((7, 11), (8, 12)),
        "medium": ((11, 18), (12, 19)),
        "hard": ((16, 24), (17, 25)),
    }
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    (hlo, hhi), (wlo, whi) = bands[difficulty]
    h = _draw_int_axis(ctx, "grid_h", 6, 30, hlo, hhi, overrides)
    w = _draw_int_axis(ctx, "grid_w", 6, 30, wlo, whi, overrides)
    scheduled = tuple(SHAPES)[(seed + sample_index) % len(SHAPES)]
    texture = _draw_choice_axis(ctx, "texture", SHAPES, (scheduled,), overrides)
    palette_kind = _draw_choice_axis(ctx, "palette_kind", PALETTES, PALETTES, overrides)
    if overrides.get("object_color") is not None:
        color = overrides["object_color"]
        if type(color) is not int or color not in range(1, 9):
            raise ValueError("object_color must be an exact integer in 1..8")
        color = ctx.draw_choice("object_color", tuple(range(1, 9)))
    else:
        color = ctx.draw_choice("object_color", PALETTES[palette_kind])

    shape = SHAPES[texture]
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    if sh > h or sw > w or (sh == h and sw == w):
        raise ValueError("selected texture does not leave a legal marker position")
    placements = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
    rng = ctx.draw_rng("placement")
    source_choices = placements[:]
    rng.shuffle(source_choices)
    selected = None
    for sr, sc in source_choices:
        marker_choices = [(mr, mc) for mr, mc in placements
                          if not (sr <= mr <= sr + sh - 1 and sc <= mc <= sc + sw - 1)]
        if marker_choices:
            selected = (sr, sc, rng.choice(marker_choices))
            break
    if selected is None:
        raise ValueError("no separated source and destination placement exists")
    sr, sc, marker = selected
    grid = full_grid(h, w, 0)
    for dr, dc in shape:
        grid[sr + dr][sc + dc] = color
    grid[marker[0]][marker[1]] = 9
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructive generator produced invalid grid: " + "; ".join(errors))
    return grid
