"""Generator for hard_j19 — select one body object, then transform its crop.

Canonical rule:
* the top-left marker is the selected object color;
* the top-right marker is a transform code (1 identity, 2 clockwise,
  3 left/right reflection, 4 transpose, 5 half-turn);
* body objects are separated monochromatic 4-connected blobs;
* exactly one body object has the selector color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "346480121fcb"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "33dfe7b5a888"
SUMMARY = (
    "A selector marker at the upper-left names one body object's color and a "
    "transform marker at the upper-right names the operation. Crop the unique "
    "selector-colored 4-connected body object, apply key 1=identity, 2=rotate-CW, "
    "3=flip-LR, 4=transpose, or 5=rotate-180, then crop to content."
)

INVARIANTS = [
    "rectangular exact-integer ARC grid with a header row",
    "selector at (0,0) is one of 2..7 and transform key at (0,w-1) is 1..5",
    "the body contains exactly one selector-colored 4-connected object and at least one decoy",
]

# Only advertise caller controls that are implemented and independently probed.
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-skewed 6..14", "valid": "6..14"},
    "grid_w": {"type": "int", "default": "difficulty-skewed 9..16", "valid": "9..16"},
    "key": {"type": "int", "default": "rng 1..5", "valid": "1..5"},
    "blob_count": {"type": "int", "default": "rng 2..4", "valid": "2..4"},
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid: list[list[int]]) -> list[dict]:
    """Return monochromatic nonzero 4-connected body objects in scan order."""
    pending = {
        (row, column)
        for row in range(1, len(grid))
        for column in range(len(grid[0]))
        if grid[row][column] != 0
    }
    result = []
    while pending:
        start = min(pending)
        pending.remove(start)
        color = grid[start[0]][start[1]]
        stack = [start]
        cells = []
        while stack:
            point = stack.pop()
            cells.append(point)
            for dr, dc in _CARDINAL:
                neighbor = (point[0] + dr, point[1] + dc)
                if neighbor in pending and grid[neighbor[0]][neighbor[1]] == color:
                    pending.remove(neighbor)
                    stack.append(neighbor)
        result.append({"color": color, "cells": sorted(cells)})
    result.sort(key=lambda item: item["cells"][0])
    return result


def observe_overrides(grid: list[list[int]]) -> dict[str, int]:
    """Recover every declared override from a valid returned grid."""
    if (
        type(grid) is not list
        or not grid
        or type(grid[0]) is not list
        or not grid[0]
        or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
    ):
        raise ValueError("grid must be a nonempty rectangle")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "key": grid[0][-1],
        "blob_count": len(_components(grid)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical input grammar."""
    errors: list[str] = []
    if (
        type(grid) is not list
        or not grid
        or type(grid[0]) is not list
        or not grid[0]
        or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
    ):
        return ["grid must be a nonempty rectangle"]
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        return ["grid cells must be exact integer colors 0..9"]
    height, width = len(grid), len(grid[0])
    if not 6 <= height <= 14 or not 9 <= width <= 16:
        errors.append(f"grid dimensions {height}x{width} outside 6..14 by 9..16")
    selector = grid[0][0]
    key = grid[0][-1]
    if selector not in (2, 3, 4, 5, 6, 7):
        errors.append(f"selector at (0,0) = {selector}, expected one of 2..7")
    if key not in (1, 2, 3, 4, 5):
        errors.append(f"key at (0,{width - 1}) = {key}, expected 1..5")
    if any(grid[0][column] != 0 for column in range(1, width - 1)):
        errors.append("header interior must be background")
    objects = _components(grid)
    if selector in (2, 3, 4, 5, 6, 7):
        matches = [obj for obj in objects if obj["color"] == selector]
        if len(matches) != 1:
            errors.append(f"body must contain exactly one selector-colored component; found {len(matches)}")
    if len(objects) < 2:
        errors.append("body must contain a selected object and at least one decoy")
    expected_count = (meta or {}).get("blob_count")
    if expected_count is not None and len(objects) != expected_count:
        errors.append(f"body component count {len(objects)} differs from requested {expected_count}")
    return errors


def _validate_overrides(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override key(s): " + ", ".join(unknown))
    integer_domains = {"grid_h": (6, 14), "grid_w": (9, 16), "key": (1, 5), "blob_count": (2, 4)}
    for name, (low, high) in integer_domains.items():
        value = overrides.get(name)
        if value is not None:
            if type(value) is not int:
                raise TypeError(f"{name} override must be an exact integer (bool is forbidden)")
            if not low <= value <= high:
                raise ValueError(f"{name} override {value} outside {low}..{high}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    # Full declared domains remain legal under every difficulty; draw_int_diff
    # changes only the ordinary size distribution.
    height = ctx.draw_int_diff("grid_h", 6, 14)
    width = ctx.draw_int_diff("grid_w", 9, 16)
    key = ctx.draw_int_strict("key", 1, 5)
    blob_count = ctx.draw_int_strict("blob_count", 2, 4)
    selector = ctx.draw_rng("selector").choice((2, 3, 4, 5, 6, 7))
    layout_rng = ctx.draw_rng("layout")
    decoy_colors = layout_rng.sample(
        [color for color in range(1, 10) if color != selector], blob_count - 1
    )

    for _scene_attempt in range(160):
        grid = full_grid(height, width, 0)
        grid[0][0] = selector
        grid[0][-1] = key
        occupied: set[tuple[int, int]] = set()
        selected_size = layout_rng.randint(3, 7)
        if not _place_blob(grid, layout_rng, _rand_blob(layout_rng, selected_size), selector, occupied):
            continue
        placed = True
        for color in decoy_colors:
            size = layout_rng.randint(2, 5)
            if not _place_blob(grid, layout_rng, _rand_blob(layout_rng, size), color, occupied):
                placed = False
                break
        if placed and not self_check(grid, difficulty=difficulty, meta={"blob_count": blob_count}):
            return grid
    raise RuntimeError("unable to construct a valid selector/transform scene")


def _rand_blob(rng, size: int) -> list[tuple[int, int]]:
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < size:
        row, column = rng.choice(cells)
        dr, dc = rng.choice(_CARDINAL)
        neighbor = (row + dr, column + dc)
        if neighbor not in seen:
            cells.append(neighbor)
            seen.add(neighbor)
    min_row = min(row for row, _ in cells)
    min_column = min(column for _, column in cells)
    return sorted((row - min_row, column - min_column) for row, column in cells)


def _place_blob(grid, rng, shape, color, occupied) -> bool:
    height, width = len(grid), len(grid[0])
    shape_height = max(row for row, _ in shape) + 1
    shape_width = max(column for _, column in shape) + 1
    if shape_height > height - 1 or shape_width > width:
        return False
    for _ in range(160):
        row0 = rng.randint(1, height - shape_height)
        column0 = rng.randint(0, width - shape_width)
        cells = {(row0 + dr, column0 + dc) for dr, dc in shape}
        halo = {
            (row + dr, column + dc)
            for row, column in cells
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if 1 <= row + dr < height and 0 <= column + dc < width
        }
        if halo.isdisjoint(occupied):
            for row, column in cells:
                grid[row][column] = color
            occupied.update(cells)
            return True
    return False
