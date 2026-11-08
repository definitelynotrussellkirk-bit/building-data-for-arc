"""Inputs for 564cab531f76, bound to the unchanged canonical Racket rule.

Four distinct singleton colors mark the canvas corners.  Every other
same-color 4-connected object is recolored by the nearest corner to the
object's *bounding-box center*, using doubled Manhattan coordinates.  Exact
ties choose top before bottom and left before right (NW, NE, SW, SE order).

This module emits inputs only.  ``_semantic_oracle`` and the rival functions
are diagnostic contracts; exported labels still come from canonical Racket.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "564cab531f76"
TASK_ID = "564cab531f76"
RULE_HASH = "ef9264e6f3e7"
VERSION = "2.0.0"
SUMMARY = (
    "Four distinct singleton colors mark the four grid corners. Each other "
    "monochromatic 4-connected object is recolored by the marker nearest its "
    "tight bounding-box center, measured with doubled Manhattan coordinates. "
    "Exact ties choose top, then left. Every five-draw schedule includes two "
    "canonical-scale examples and three asymmetric center-line witnesses that "
    "separate this rule from anchor, centroid, nearest-pixel, and opposite-tie shortcuts."
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is color 0 and all object cells lie strictly inside the border",
    "the four corners are distinct nonzero singleton markers",
    "there are 2..5 uniquely colored 4-connected non-corner objects",
    "every five consecutive default draws cover canonical scale and refute all declared rivals",
]
AXES = {
    "grid_h": {"type": "int", "default": "profile-conditioned", "valid": "6..14"},
    "grid_w": {"type": "int", "default": "profile-conditioned", "valid": "6..14"},
    "n_blobs": {"type": "int", "default": "profile-conditioned", "valid": "2..5"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PERIOD = 5
SCHEDULE_PROFILES = ("canonical_scale", "square", "wide", "tall")
_SCHEDULE = ("canonical_scale", "canonical_scale", "square", "wide", "tall")


def schedule_profile(seed, sample_index, difficulty=None):
    del difficulty
    return _SCHEDULE[(int(seed) + int(sample_index)) % SCHEDULE_PERIOD]


def _axis(ctx, name, defaults, legal):
    """Consume an exact caller override through the same declared draw label."""
    options = tuple(legal) if name in ctx.overrides else tuple(defaults)
    return ctx.draw_choice(name, options)


def _default_dimensions(ctx, profile, difficulty):
    if profile == "canonical_scale":
        return 6, 6
    if profile == "square":
        options = {
            "easy": (7, 8, 9),
            "medium": (8, 9, 10, 11, 12),
            "hard": (10, 11, 12, 13, 14),
            None: (7, 8, 9, 10, 11, 12, 13, 14),
        }[difficulty]
        side = ctx.draw_choice("square_side", options)
        return side, side
    pairs = {
        "easy": ((6, 9), (6, 10), (7, 10), (7, 11), (8, 11)),
        "medium": ((6, 11), (7, 12), (8, 12), (8, 13), (9, 14), (10, 14)),
        "hard": ((6, 13), (7, 14), (8, 14), (9, 14), (10, 14), (11, 14)),
        None: ((6, 9), (6, 11), (7, 12), (8, 13), (9, 14), (10, 14), (11, 14)),
    }[difficulty]
    short, long = ctx.draw_choice("rectangular_dimensions", pairs)
    return (short, long) if profile == "wide" else (long, short)


def _canonical_primary(height, width):
    """A canonical-scale domino; at 6x6 its bbox is exactly left/right tied."""
    col0 = (width - 2) // 2
    return ((1, col0), (1, col0 + 1))


def _primary_witness(height, width):
    """A four-cell asymmetric center witness valid for every declared size.

    Even widths use an exact left/right tie whose correct target is southwest;
    odd widths use an exact top/bottom tie whose target is northeast.  In both
    cases top-left, bottom-right, centroid, first-pixel, nearest-pixel, and
    opposite-tie rules all choose another corner.
    """
    if width % 2 == 0:
        row0 = (height - 1) // 2
        col0, col1 = width // 2 - 1, width // 2
        return tuple(sorted({
            (row0, col0), (row0, col1),
            (row0 + 1, col1), (row0 + 2, col1),
        }))
    col0 = width // 2
    if height % 2 == 0:
        row0, row1 = height // 2 - 1, height // 2
        return tuple(sorted({
            (row0, col0), (row1, col0),
            (row1, col0 + 1), (row1, col0 + 2),
        }))
    row0 = height // 2
    return tuple(sorted({
        (row0 - 1, col0), (row0, col0),
        (row0 + 1, col0), (row0 + 1, col0 + 1),
    }))


def _point_corner_index(row, col, height, width):
    return 2 * int(2 * row > height - 1) + int(2 * col > width - 1)


def _extra_blob_cells(ctx, height, width, used, count):
    """Place one singleton in each target quadrant before repeating."""
    desired = (2, 0, 3, 1)  # SW, NW, SE, NE; primary already targets NE.
    result = []
    for index in range(count):
        target = desired[index % len(desired)]
        candidates = [
            (row, col)
            for row in range(1, height - 1)
            for col in range(1, width - 1)
            if (row, col) not in used
            and _point_corner_index(row, col, height, width) == target
        ]
        if not candidates:
            raise ValueError(
                f"no interior placement for blob {index + 2} in {height}x{width}"
            )
        point = ctx.draw_choice(f"blob_{index + 2}_cell", tuple(candidates))
        used.add(point)
        result.append((point,))
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    for name, value in overrides.items():
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w = _default_dimensions(ctx, profile, difficulty)
    height = _axis(ctx, "grid_h", (default_h,), range(6, 15))
    width = _axis(ctx, "grid_w", (default_w,), range(6, 15))
    default_counts = (2, 3) if profile == "canonical_scale" else (2, 3, 4, 5)
    n_blobs = _axis(ctx, "n_blobs", default_counts, range(2, 6))

    colors = ctx.draw_distinct_colors("palette", n=4 + n_blobs, exclude=(0,))
    corner_colors, blob_colors = colors[:4], colors[4:]
    grid = full_grid(height, width, 0)
    corners = ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1))
    for (row, col), color in zip(corners, corner_colors):
        grid[row][col] = color

    primary = (_canonical_primary(height, width)
               if profile == "canonical_scale" else _primary_witness(height, width))
    used = set(corners) | set(primary)
    blobs = [primary] + _extra_blob_cells(ctx, height, width, used, n_blobs - 1)
    for cells, color in zip(blobs, blob_colors):
        for row, col in cells:
            grid[row][col] = color
    return grid


def _components(points):
    remaining = set(points)
    groups = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        group, stack = {first}, [first]
        while stack:
            row, col = stack.pop()
            for point in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if point in remaining:
                    remaining.remove(point)
                    group.add(point)
                    stack.append(point)
        groups.append(tuple(sorted(group)))
    return groups


def _objects(grid):
    by_color = {}
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color:
                by_color.setdefault(color, set()).add((row, col))
    result = []
    for color in sorted(by_color):
        for cells in _components(by_color[color]):
            rows = [row for row, _ in cells]
            cols = [col for _, col in cells]
            result.append({
                "color": color,
                "cells": cells,
                "r1": min(rows),
                "r2": max(rows),
                "c1": min(cols),
                "c2": max(cols),
            })
    return result


def _split_objects(grid):
    height, width = len(grid), len(grid[0])
    corners = ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1))
    corner_set = set(corners)
    corner_objects, blobs = [], []
    for obj in _objects(grid):
        if len(obj["cells"]) == 1 and obj["cells"][0] in corner_set:
            corner_objects.append(obj)
        else:
            blobs.append(obj)
    return corners, corner_objects, blobs


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    errors = []
    if not (6 <= height <= 14 and 6 <= width <= 14):
        errors.append(f"grid dimensions must be in 6..14, got {height}x{width}")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        errors.append("cells must be integer colors in 0..9")
        return errors

    corners = ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1))
    corner_colors = [grid[row][col] for row, col in corners]
    if any(color == 0 for color in corner_colors):
        errors.append("all four corner markers must be nonzero")
    if len(set(corner_colors)) != 4:
        errors.append(f"corner markers must have four distinct colors: {corner_colors}")
    for point, color in zip(corners, corner_colors):
        if color and sum(cell == color for row in grid for cell in row) != 1:
            errors.append(f"corner color {color} must occur only at {point}")

    if not any(cell == 0 for row in grid for cell in row):
        errors.append("zero background must be present")
    if errors:
        return errors
    _, corner_objects, blobs = _split_objects(grid)
    if len(corner_objects) != 4:
        errors.append(f"expected four singleton corner objects, got {len(corner_objects)}")
    if not (2 <= len(blobs) <= 5):
        errors.append(f"expected 2..5 non-corner objects, got {len(blobs)}")
    blob_colors = [obj["color"] for obj in blobs]
    if len(set(blob_colors)) != len(blob_colors):
        errors.append("each non-corner object must have its own color")
    if set(blob_colors) & set(corner_colors):
        errors.append("blob colors must be distinct from corner colors")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    issues = self_check(grid)
    if issues:
        raise ValueError("cannot observe malformed grid: " + "; ".join(issues))
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_blobs": len(_split_objects(grid)[2])}


def _corner_index(bottom, right):
    return 2 * int(bool(bottom)) + int(bool(right))


def _render_rule(grid, selector):
    height, width = len(grid), len(grid[0])
    corners, _, blobs = _split_objects(grid)
    out = full_grid(height, width, 0)
    for row, col in corners:
        out[row][col] = grid[row][col]
    for obj in blobs:
        index = selector(obj, height, width, corners)
        color = grid[corners[index][0]][corners[index][1]]
        for row, col in obj["cells"]:
            out[row][col] = color
    return out


def _semantic_oracle(grid):
    return _render_rule(
        grid,
        lambda obj, height, width, _corners: _corner_index(
            obj["r1"] + obj["r2"] > height - 1,
            obj["c1"] + obj["c2"] > width - 1,
        ),
    )


# Plausible wrong rules. CANONICAL_SHORTCUTS below retains only the subset
# that fits all four canonical pairs; generated witnesses cover the larger set.
def _bbox_top_left(grid):
    return _render_rule(grid, lambda obj, h, w, _: _corner_index(
        2 * obj["r1"] > h - 1, 2 * obj["c1"] > w - 1))


def _bbox_bottom_right(grid):
    return _render_rule(grid, lambda obj, h, w, _: _corner_index(
        2 * obj["r2"] > h - 1, 2 * obj["c2"] > w - 1))


def _occupied_centroid(grid):
    def selector(obj, height, width, _corners):
        count = len(obj["cells"])
        return _corner_index(
            2 * sum(row for row, _ in obj["cells"]) > count * (height - 1),
            2 * sum(col for _, col in obj["cells"]) > count * (width - 1),
        )
    return _render_rule(grid, selector)


def _first_pixel(grid):
    def selector(obj, height, width, _corners):
        row, col = min(obj["cells"])
        return _corner_index(2 * row > height - 1, 2 * col > width - 1)
    return _render_rule(grid, selector)


def _nearest_foreground_pixel_manhattan(grid):
    def selector(obj, _height, _width, corners):
        return min(range(4), key=lambda index: min(
            abs(row - corners[index][0]) + abs(col - corners[index][1])
            for row, col in obj["cells"]))
    return _render_rule(grid, selector)


def _nearest_foreground_pixel_euclidean(grid):
    def selector(obj, _height, _width, corners):
        return min(range(4), key=lambda index: min(
            (row - corners[index][0]) ** 2 + (col - corners[index][1]) ** 2
            for row, col in obj["cells"]))
    return _render_rule(grid, selector)


def _ties_bottom_right(grid):
    return _render_rule(grid, lambda obj, h, w, _: _corner_index(
        obj["r1"] + obj["r2"] >= h - 1,
        obj["c1"] + obj["c2"] >= w - 1))


def _identity(grid):
    return [list(row) for row in grid]


def _fixed_corner(index):
    return lambda grid: _render_rule(grid, lambda _obj, _h, _w, _corners: index)


CANONICAL_SHORTCUTS = {
    "bbox_top_left": _bbox_top_left,
    "occupied_centroid": _occupied_centroid,
    "first_pixel": _first_pixel,
    "nearest_foreground_pixel_manhattan": _nearest_foreground_pixel_manhattan,
    "nearest_foreground_pixel_euclidean": _nearest_foreground_pixel_euclidean,
}
SEMANTIC_RIVALS = {
    **CANONICAL_SHORTCUTS,
    "bbox_bottom_right": _bbox_bottom_right,
    "ties_bottom_right": _ties_bottom_right,
}
LESSON_COMPETITORS = {
    **SEMANTIC_RIVALS,
    "identity": _identity,
    "always_northwest": _fixed_corner(0),
    "always_northeast": _fixed_corner(1),
    "always_southwest": _fixed_corner(2),
    "always_southeast": _fixed_corner(3),
}


def _exact_tie(grid):
    height, width = len(grid), len(grid[0])
    return any(
        obj["r1"] + obj["r2"] == height - 1
        or obj["c1"] + obj["c2"] == width - 1
        for obj in _split_objects(grid)[2]
    )


def _counterexample_predicate(rival):
    def witness(grid):
        return rival(grid) != _semantic_oracle(grid)
    return witness


SEMANTIC_WITNESSES = {"bbox_center_exact_tie": _exact_tie}
WITNESS_RIVALS = {"bbox_center_exact_tie": ["ties_bottom_right"]}
for _name, _rival in SEMANTIC_RIVALS.items():
    _witness_name = "counterexample_" + _name
    SEMANTIC_WITNESSES[_witness_name] = _counterexample_predicate(_rival)
    WITNESS_RIVALS[_witness_name] = [_name]


def lesson_identifiable(demos, query):
    """Finite-rival diagnostic: every surviving rival must agree on query."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"rival {name} fits every demo but disagrees on query")
    return reasons
