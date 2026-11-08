"""Constructive sampler for a rotation-only shape/color relation matrix.

The selected Racket authority sorts nonzero objects by top-left position and
builds an N x N relation matrix.  Diagonal cells are 9; off-diagonal cells are
6 for the same rotation-class and color, 4 for the same rotation-class only,
2 for the same color only, and 0 otherwise.  Reflections are deliberately not
shape-equivalent.
"""
from __future__ import annotations

from itertools import product

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c782972f840b"
TASK_ID = GENERATOR_ID
RULE_HASH = "1f9d3ac91fc0"
VERSION = "3.0.0"

SUMMARY = (
    "A 0-background grid contains 4-6 isolated monochrome polyominoes. "
    "Objects are compared after rotation but not reflection.  Sorted by "
    "top-left position, the output relation matrix uses 9 on the diagonal, "
    "then 6/4/2/0 for same-shape+same-color / same-shape-only / "
    "same-color-only / neither."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0 and all nonzero objects are isolated and monochrome",
    "there are 4-6 connected objects using 2-3 nonzero colors",
    "at least two rotation-shape classes and both shape and color comparisons are meaningful",
    "rotation-equivalent objects may differ in orientation; reflected chiral shapes remain distinct",
    "canvas defaults cover every canonical (height, width, palette-size) profile",
]

_CANVAS_PROFILES = {
    "canonical_12x14x3": (12, 14, 2),
    "canonical_13x15x3": (13, 15, 2),
    "canonical_12x16x4": (12, 16, 3),
    "canonical_14x15x3": (14, 15, 2),
    "canonical_13x14x3": (13, 14, 2),
    # Dimensions are intentionally outside the canonical envelope so this
    # branch is observable rather than an alias of a canonical token.
    "expanded": None,
}
_CANONICAL_PROFILE_NAMES = tuple(
    name for name, value in _CANVAS_PROFILES.items() if value is not None
)
_RELATION_PROFILES = ("with_duplicate", "without_duplicate")

AXES = {
    "canvas_profile": {
        "type": "str",
        "default": "uniform over the five canonical profiles",
        "valid": "canonical_12x14x3|canonical_13x15x3|canonical_12x16x4|canonical_14x15x3|canonical_13x14x3|expanded",
    },
    "n_objects": {
        "type": "int",
        "default": "difficulty-weighted 4..6",
        "valid": "4..6",
    },
    "relation_profile": {
        "type": "str",
        "default": "with_duplicate|without_duplicate",
        "valid": "with_duplicate|without_duplicate",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# Two chiral mirror pairs.  Members of each pair share a dihedral key but not a
# rotation key, yielding an executable witness against the common reflection
# shortcut.  All shapes fit in a 3x3 box.
_MIRROR_PAIRS = (
    (
        ((0, 1), (0, 2), (1, 0), (1, 1)),       # S tetromino
        ((0, 0), (0, 1), (1, 1), (1, 2)),       # Z tetromino
    ),
    (
        ((0, 0), (1, 0), (2, 0), (2, 1)),       # L tetromino
        ((0, 1), (1, 1), (2, 0), (2, 1)),       # J tetromino
    ),
)
_THIRD_SHAPES = (
    ((0, 0), (0, 1), (0, 2), (1, 1)),           # T tetromino
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),   # U pentomino
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),   # P pentomino
    ((0, 0), (0, 1), (0, 2)),                   # line triomino
)


def _normalize_shape(points):
    points = tuple(points)
    if not points:
        return ()
    top = min(row for row, _ in points)
    left = min(col for _, col in points)
    return tuple(sorted((row - top, col - left) for row, col in points))


def _rotate_shape(shape):
    return _normalize_shape((col, -row) for row, col in shape)


def _rotate_n(shape, turns):
    result = _normalize_shape(shape)
    for _ in range(turns % 4):
        result = _rotate_shape(result)
    return result


def _rotation_key(shape):
    variants = []
    current = _normalize_shape(shape)
    for _ in range(4):
        variants.append(current)
        current = _rotate_shape(current)
    return min(variants)


def _dihedral_key(shape):
    shape = _normalize_shape(shape)
    reflected = _normalize_shape((row, -col) for row, col in shape)
    return min(_rotation_key(shape), _rotation_key(reflected))


def _shape_size(shape):
    return (
        max(row for row, _ in shape) + 1,
        max(col for _, col in shape) + 1,
    )


def _components(grid):
    """Return 4-connected nonzero objects, joining touching colors first."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    items = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and grid[rr][cc] != 0
                        and (rr, cc) not in seen
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            colors = {grid[r][c] for r, c in cells}
            shape = _normalize_shape(cells)
            items.append(
                {
                    "cells": tuple(sorted(cells)),
                    "bbox": (
                        min(r for r, _ in cells),
                        min(c for _, c in cells),
                        max(r for r, _ in cells),
                        max(c for _, c in cells),
                    ),
                    "color": next(iter(colors)) if len(colors) == 1 else None,
                    "colors": frozenset(colors),
                    "oriented": shape,
                    "rotation": _rotation_key(shape),
                    "dihedral": _dihedral_key(shape),
                }
            )
    return sorted(items, key=lambda item: item["bbox"][:2])


def _relation_output(grid, *, equivalence="rotation"):
    """Independent Python rendering of the selected relation semantics."""
    items = _components(grid)
    size = len(items)
    result = [[0] * size for _ in range(size)]
    for row, left in enumerate(items):
        for col, right in enumerate(items):
            if row == col:
                result[row][col] = 9
                continue
            if equivalence == "rotation":
                same_shape = left["rotation"] == right["rotation"]
            elif equivalence == "dihedral":
                same_shape = left["dihedral"] == right["dihedral"]
            elif equivalence == "oriented":
                same_shape = left["oriented"] == right["oriented"]
            else:
                raise ValueError(f"unknown equivalence {equivalence!r}")
            same_color = left["color"] == right["color"]
            result[row][col] = (
                6 if same_shape and same_color
                else 4 if same_shape
                else 2 if same_color
                else 0
            )
    return result


def _choose_canvas(ctx, overrides):
    options = (
        tuple(_CANVAS_PROFILES)
        if "canvas_profile" in overrides
        else _CANONICAL_PROFILE_NAMES
    )
    profile = ctx.draw_choice("canvas_profile", options)
    fixed = _CANVAS_PROFILES[profile]
    if fixed is not None:
        return profile, fixed
    # Expanded dimensions never alias any canonical profile.
    height = ctx.draw_int("expanded_h", 16, 18)
    width = ctx.draw_int("expanded_w", 18, 20)
    n_colors = ctx.draw_choice("expanded_n_colors", (2, 3))
    return profile, (height, width, n_colors)


def _draw_n_objects(ctx):
    if ctx.difficulty == "easy":
        choices = (4, 4, 4, 5, 5, 6)
    elif ctx.difficulty == "hard":
        choices = (4, 5, 5, 6, 6, 6)
    else:
        choices = (4, 4, 5, 5, 6, 6)
    return ctx.draw_choice("n_objects", choices)


def _draw_relation_profile(ctx):
    if ctx.difficulty == "easy":
        choices = ("with_duplicate", "with_duplicate", "without_duplicate")
    elif ctx.difficulty == "hard":
        choices = ("with_duplicate", "without_duplicate", "without_duplicate")
    else:
        choices = _RELATION_PROFILES
    return ctx.draw_choice("relation_profile", choices)


def _assign_shape_colors(n_objects, n_colors, relation_profile, rng):
    """Construct exact relation branches, then fill from remaining pairs."""
    if relation_profile == "with_duplicate":
        if n_colors == 2:
            assignments = [(0, 0), (0, 0), (0, 1), (1, 0)]
        else:
            assignments = [(0, 0), (0, 0), (0, 1), (1, 2)]
            if n_objects >= 5:
                assignments.append((1, 0))
        candidates = list(product(range(3), range(n_colors)))
        rng.shuffle(candidates)
        while len(assignments) < n_objects:
            unused = [item for item in candidates if item not in assignments]
            assignments.append((unused or candidates)[0])
    elif relation_profile == "without_duplicate":
        if n_colors == 2:
            assignments = [(0, 0), (0, 1), (1, 0), (1, 1)]
        else:
            assignments = [(0, 0), (0, 1), (1, 0), (2, 2)]
        candidates = [
            item
            for item in product(range(3), range(n_colors))
            if item not in assignments
        ]
        rng.shuffle(candidates)
        assignments.extend(candidates[: n_objects - len(assignments)])
    else:
        raise ValueError(f"unknown relation_profile {relation_profile!r}")
    if len(assignments) != n_objects:
        raise ValueError("could not construct requested object relation profile")
    rng.shuffle(assignments)
    return assignments


def _free_bbox(grid, row, col, shape):
    height, width = len(grid), len(grid[0])
    shape_h, shape_w = _shape_size(shape)
    if row < 0 or col < 0 or row + shape_h > height or col + shape_w > width:
        return False
    for rr in range(max(0, row - 1), min(height, row + shape_h + 1)):
        for cc in range(max(0, col - 1), min(width, col + shape_w + 1)):
            if grid[rr][cc] != 0:
                return False
    return True


def _place_objects(height, width, placements, rng):
    """Place at most six <=3x3 objects in separated 2x3 spatial slots."""
    base_rows = (0, height // 2 + 1)
    base_cols = (0, width // 3 + 1, 2 * width // 3 + 1)
    slots = [(row, col) for row in base_rows for col in base_cols]
    rng.shuffle(slots)
    grid = full_grid(height, width, 0)
    for (shape, color), (base_row, base_col) in zip(placements, slots):
        candidates = [
            (base_row + dr, base_col + dc)
            for dr in (0, 1)
            for dc in (0, 1)
        ]
        rng.shuffle(candidates)
        for row, col in candidates:
            if _free_bbox(grid, row, col, shape):
                for drow, dcol in shape:
                    grid[row + drow][col + dcol] = color
                break
        else:
            raise ValueError("constructive slot placement unexpectedly failed")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise KeyError(f"unknown override axis/axes: {', '.join(unknown)}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    _profile, (height, width, n_colors) = _choose_canvas(ctx, overrides)
    n_objects = _draw_n_objects(ctx)
    relation_profile = _draw_relation_profile(ctx)

    palette = ctx.draw_rng("palette").sample(list(range(1, 10)), n_colors)
    shape_rng = ctx.draw_rng("shape_family")
    mirror_a, mirror_b = shape_rng.choice(_MIRROR_PAIRS)
    third = shape_rng.choice(_THIRD_SHAPES)
    shape_classes = (mirror_a, mirror_b, third)

    assignment_rng = ctx.draw_rng("assignments")
    assignments = _assign_shape_colors(
        n_objects, n_colors, relation_profile, assignment_rng
    )
    offsets = [ctx.draw_rng(f"rotation_offset_{index}").randrange(4) for index in range(3)]
    occurrences = [0, 0, 0]
    placements = []
    for shape_index, color_index in assignments:
        turns = offsets[shape_index] + occurrences[shape_index]
        occurrences[shape_index] += 1
        placements.append(
            (_rotate_n(shape_classes[shape_index], turns), palette[color_index])
        )

    return _place_objects(height, width, placements, ctx.draw_rng("layout"))


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"]
    if not 8 <= len(grid) <= 30 or not 8 <= width <= 30:
        errors.append(f"grid dimensions {len(grid)}x{width} outside supported 8..30")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return errors + ["grid values must be integer ARC colors 0..9"]

    items = _components(grid)
    if not 4 <= len(items) <= 6:
        errors.append(f"expected 4..6 objects, found {len(items)}")
    if any(item["color"] is None for item in items):
        errors.append("touching nonzero colors form a multicolor object")
    for index, item in enumerate(items):
        size = len(item["cells"])
        top, left, bottom, right = item["bbox"]
        if not 3 <= size <= 7:
            errors.append(f"object {index} size {size} outside 3..7")
        if bottom - top + 1 > 3 or right - left + 1 > 3:
            errors.append(f"object {index} bounding box exceeds 3x3")

    colors = {item["color"] for item in items if item["color"] is not None}
    shape_classes = {item["rotation"] for item in items}
    if not 2 <= len(colors) <= 3:
        errors.append(f"expected 2..3 nonzero colors, found {len(colors)}")
    if not 2 <= len(shape_classes) <= 3:
        errors.append(f"expected 2..3 rotation-shape classes, found {len(shape_classes)}")

    if len(items) >= 2 and all(item["color"] is not None for item in items):
        pairs = [
            (
                left["rotation"] == right["rotation"],
                left["color"] == right["color"],
            )
            for index, left in enumerate(items)
            for right in items[index + 1 :]
        ]
        if not any(same_shape for same_shape, _ in pairs):
            errors.append("no pair shares a shape up to rotation")
        if not any(same_color for _, same_color in pairs):
            errors.append("no pair shares a color")
        if not any(not same_shape and not same_color for same_shape, same_color in pairs):
            errors.append("no pair differs in both shape and color")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    items = _components(grid)
    profile_key = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
    profile = next(
        (
            name
            for name, dimensions in _CANVAS_PROFILES.items()
            if dimensions is not None
            and (dimensions[0], dimensions[1], dimensions[2] + 1) == profile_key
        ),
        "expanded",
    )
    has_duplicate = any(
        left["rotation"] == right["rotation"] and left["color"] == right["color"]
        for index, left in enumerate(items)
        for right in items[index + 1 :]
    )
    return {
        "canvas_profile": profile,
        "n_objects": len(items),
        "relation_profile": "with_duplicate" if has_duplicate else "without_duplicate",
    }


def _mirror_not_rotation(grid):
    items = _components(grid)
    return any(
        left["rotation"] != right["rotation"]
        and left["dihedral"] == right["dihedral"]
        for index, left in enumerate(items)
        for right in items[index + 1 :]
    )


def _dihedral_equivalence(grid):
    return _relation_output(grid, equivalence="dihedral")


SEMANTIC_WITNESSES = {"mirror_not_rotation": _mirror_not_rotation}
SEMANTIC_RIVALS = {"dihedral_equivalence": _dihedral_equivalence}
WITNESS_RIVALS = {"mirror_not_rotation": ["dihedral_equivalence"]}
CANONICAL_SHORTCUTS = {"dihedral_equivalence": _dihedral_equivalence}
LESSON_COMPETITORS = {"dihedral_equivalence": _dihedral_equivalence}
