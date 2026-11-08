"""Generator for d4be41674012 — left-to-right transpose and vertical packing.

The input contains three separated monochrome objects.  Read them by increasing
left edge, crop each bounding box, transpose the crop, and stack the transformed
pieces top-to-bottom with one blank row between adjacent pieces.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d4be41674012"
VERSION = "2.0.0"
TASK_ID = "d4be41674012"
RULE_HASH = "30576a22d996"

SUMMARY = (
    "Sort three separated objects by their left edge, transpose each cropped "
    "object, then stack the pieces vertically with one blank row between them."
)

INVARIANTS = [
    "background is color 0",
    "exactly three nonzero 4-connected same-color objects are present",
    "object bounding boxes have distinct left edges",
    "every object is quarter-turn asymmetric and at least one changes under transpose",
    "the packed output stays within the ARC 30x30 bound",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware rng 7..30", "valid": "7..30"},
    "grid_w": {"type": "int", "default": "difficulty-aware rng 9..30", "valid": "9..30"},
    "color_count": {"type": "int", "default": "rng 1..3", "valid": "1..3"},
}

_VALID_H = (7, 30)
_VALID_W = (9, 30)
_VALID_COLORS = (1, 3)

# Connected asymmetric masks.  Easy generation uses the canonical 2x2 L family;
# larger bands add rectangular and bent shapes while preserving the same rule.
_L_MASKS = (
    ((1, 1), (0, 1)),
    ((1, 0), (1, 1)),
    ((0, 1), (1, 1)),
    ((1, 1), (1, 0)),
)
_MEDIUM_MASKS = _L_MASKS + (
    ((1, 1, 0), (0, 1, 1)),
    ((0, 1, 1), (1, 1, 0)),
    ((1, 1, 1), (1, 0, 0)),
    ((1, 0), (1, 0), (1, 1)),
)
_HARD_MASKS = _MEDIUM_MASKS + (
    ((1, 1, 0), (0, 1, 0), (0, 1, 1)),
    ((0, 1, 1), (0, 1, 0), (1, 1, 0)),
    ((1, 1, 1, 0), (0, 0, 1, 1)),
    ((1, 0), (1, 0), (1, 1), (0, 1)),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in AXES:
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    for name, bounds in (("grid_h", _VALID_H), ("grid_w", _VALID_W), ("color_count", _VALID_COLORS)):
        value = overrides.get(name)
        if value is not None and not bounds[0] <= value <= bounds[1]:
            raise ValueError(f"{name} must be in {bounds[0]}..{bounds[1]}")


def _coerce_grid(grid):
    return [
        [int(value) if isinstance(value, str) and value.isdigit() else value for value in row]
        for row in grid
    ]


def _components4(grid):
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    objects = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        queue = deque([start])
        cells = {start}
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (row + dr, col + dc)
                if neighbor in unseen and grid[neighbor[0]][neighbor[1]] == color:
                    unseen.remove(neighbor)
                    cells.add(neighbor)
                    queue.append(neighbor)
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
        crop = [values[c1 : c2 + 1] for values in grid[r1 : r2 + 1]]
        objects.append({
            "color": color,
            "cells": frozenset(cells),
            "r1": r1,
            "r2": r2,
            "c1": c1,
            "c2": c2,
            "crop": crop,
        })
    return sorted(objects, key=lambda obj: (obj["c1"], obj["r1"], obj["color"]))


def _transpose(grid):
    return [list(row) for row in zip(*grid, strict=True)]


def _rotate_clockwise(grid):
    return [list(row) for row in zip(*grid[::-1], strict=True)]


def _pack(pieces):
    height = sum(len(piece) for piece in pieces) + max(0, len(pieces) - 1)
    width = max(len(piece[0]) for piece in pieces)
    output = full_grid(height, width, 0)
    row0 = 0
    for piece in pieces:
        for row, values in enumerate(piece):
            for col, value in enumerate(values):
                if value != 0:
                    output[row0 + row][col] = value
        row0 += len(piece) + 1
    return output


def _analyze_scene(grid):
    coerced = _coerce_grid(grid)
    objects = _components4(coerced)
    return {
        "grid": coerced,
        "height": len(coerced),
        "width": len(coerced[0]) if coerced else 0,
        "objects": objects,
        "colors": frozenset(obj["color"] for obj in objects),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not all(isinstance(row, (list, str)) and row for row in grid):
        return ["grid rows must be non-empty lists or digit strings"]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return ["grid must be rectangular"]
    errors = []
    height = len(coerced)
    if not (1 <= height <= 30 and 1 <= width <= 30):
        errors.append("grid dimensions must be in 1..30")
    if any(type(value) is not int or not 0 <= value <= 9 for row in coerced for value in row):
        errors.append("grid values must be integer ARC colors 0..9")
        return errors
    scene = _analyze_scene(coerced)
    objects = scene["objects"]
    if len(objects) != 3:
        errors.append(f"scene must contain exactly three same-color 4-connected components; found {len(objects)}")
        return errors
    lefts = [obj["c1"] for obj in objects]
    if len(set(lefts)) != 3:
        errors.append("object bounding boxes must have distinct left edges")
    transpose_visible = False
    for obj in objects:
        crop = obj["crop"]
        if len(crop) < 2 or len(crop[0]) < 2:
            errors.append("each object crop must span at least 2x2")
        if crop == _rotate_clockwise(crop):
            errors.append("each object must be asymmetric under clockwise rotation")
        if crop != _transpose(crop):
            transpose_visible = True
    if not transpose_visible:
        errors.append("at least one object must visibly change under transpose")
    pieces = [_transpose(obj["crop"]) for obj in objects]
    out_h = sum(len(piece) for piece in pieces) + 2
    out_w = max(len(piece[0]) for piece in pieces)
    if out_h > 30 or out_w > 30:
        errors.append("packed output must fit within 30x30")
    return errors


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    return {
        "grid_h": scene["height"],
        "grid_w": scene["width"],
        "color_count": len(scene["colors"]),
    }


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    objects = _analyze_scene(grid)["objects"]
    return _pack([_transpose(obj["crop"]) for obj in objects])


def rule_rotate_clockwise(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    objects = _analyze_scene(grid)["objects"]
    return _pack([_rotate_clockwise(obj["crop"]) for obj in objects])


def _choose_masks(rng, difficulty, height, width):
    pool = _L_MASKS if difficulty == "easy" else _HARD_MASKS if difficulty == "hard" else _MEDIUM_MASKS
    choices = list(pool)
    rng.shuffle(choices)
    selected = choices[:3]
    if sum(len(mask[0]) for mask in selected) + 2 > width or max(len(mask) for mask in selected) > height:
        selected = list(_L_MASKS[:3])
    return selected


def _distribute_slack(rng, amount, buckets):
    values = [0] * buckets
    for _ in range(amount):
        values[rng.randrange(buckets)] += 1
    return values


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty or "medium"
    default_h = {"easy": (7, 12), "medium": (9, 20), "hard": (16, 30)}[band]
    default_w = {"easy": (9, 15), "medium": (12, 24), "hard": (20, 30)}[band]
    height = ctx.draw_int("grid_h", *(default_h if overrides.get("grid_h") is None else _VALID_H))
    width = ctx.draw_int("grid_w", *(default_w if overrides.get("grid_w") is None else _VALID_W))
    color_count = ctx.draw_int("color_count", *_VALID_COLORS)
    rng = ctx.draw_rng("layout")

    masks = _choose_masks(rng, band, height, width)
    total_width = sum(len(mask[0]) for mask in masks) + 2
    if total_width > width:
        raise AssertionError("selected masks do not fit the requested width")
    extras = _distribute_slack(rng, width - total_width, 4)
    starts = []
    col = extras[0]
    for index, mask in enumerate(masks):
        starts.append(col)
        col += len(mask[0])
        if index < 2:
            col += 1 + extras[index + 1]

    palette = rng.sample(range(1, 10), color_count)
    colors = [palette[index % color_count] for index in range(3)]
    rng.shuffle(colors)
    grid = full_grid(height, width, 0)
    for mask, col0, color in zip(masks, starts, colors, strict=True):
        row0 = rng.randint(0, height - len(mask))
        for dr, row in enumerate(mask):
            for dc, occupied in enumerate(row):
                if occupied:
                    grid[row0 + dr][col0 + dc] = color

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
