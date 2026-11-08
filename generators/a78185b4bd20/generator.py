"""Generator for a78185b4bd20 — select the first LR-symmetric component.

The pinned Racket authority scans monochrome 4-connected components in
row-major order.  It selects the first component whose full bounding-box crop
is invariant under a left-right flip, crops that box, and recolors every
nonzero cell cyan (8).  If no component qualifies, it returns ``[[0]]``.

The canonical data uses three- and five-component scenes.  A four-step lesson
schedule covers both counts.  Its five-component scenes pair the selected
component with a later LR-symmetric component of the same color; one makes the
first candidate larger and one makes it smaller.  Its three-component scenes
mirror the canonical single-candidate layout.  Together they teach component
order without drifting away from canonical scene structure.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "a78185b4bd20"
TASK_ID = GENERATOR_ID
RULE_HASH = "4f60736ed86a"
VERSION = "3.2.0"
EXAMPLES_NEEDED = 3
EXPECTED_OUTPUT_CODOMAIN = 9
SUMMARY = (
    "Scan monochrome 4-connected components in row-major order, select the "
    "first component whose bounding-box crop is left-right symmetric, crop it, "
    "and recolor every nonzero cell to cyan(8). A four-step schedule covers "
    "the canonical three- and five-component scene counts; three-component "
    "lessons anchor the canonical 11x11 four-color profile, and five-component "
    "lessons add a later same-color symmetric competitor so order, not size "
    "or color alone, determines the answer."
)

INVARIANTS = [
    "background is color 0",
    "components are monochrome and 4-connected, ordered by first row-major cell",
    "at least one LR-symmetric and one LR-asymmetric component are present",
    "an LR-asymmetric distractor follows the selected component",
    "generated object counts alternate across the canonical support {3, 5}",
    "three-object defaults use the canonical 11x11 four-color profile",
    "five-object scenes contain a later same-color LR-symmetric competitor",
    "the two five-object profiles reverse selected-versus-competitor size order",
]

# Only exact, observable caller controls are declared. Shape, palette, placement,
# and curriculum profile are deterministic nuisance variation, not public axes.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "11 for three-object profiles; rng 7..14 otherwise",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "11 for three-object profiles; rng 9..16 otherwise",
        "valid": "9..16",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# Normalized shapes, all within 3x3.  Reflection of any shape in these banks
# preserves its symmetric/asymmetric role.
_SINGLETON = ((0, 0),)
_VERTICAL_DOMINO = ((0, 0), (1, 0))
_HORIZONTAL_DOMINO = ((0, 0), (0, 1))
_T4 = ((0, 0), (0, 1), (0, 2), (1, 1))
_PLUS5 = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
_U7 = ((0, 0), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2))
_HOLLOW8 = (
    (0, 0), (0, 1), (0, 2),
    (1, 0),         (1, 2),
    (2, 0), (2, 1), (2, 2),
)

_L3 = ((0, 0), (1, 0), (1, 1))
_J4 = ((0, 0), (0, 1), (1, 0), (2, 0))
_STAIR4 = ((0, 0), (0, 1), (1, 1), (1, 2))
_P5 = ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1))

_SMALL_BY_DIFFICULTY = {
    "easy": (_SINGLETON, _VERTICAL_DOMINO),
    "medium": (_SINGLETON, _VERTICAL_DOMINO, _HORIZONTAL_DOMINO, _T4),
    "hard": (_HORIZONTAL_DOMINO, _T4),
    None: (_SINGLETON, _VERTICAL_DOMINO, _HORIZONTAL_DOMINO, _T4),
}
_LARGE_BY_DIFFICULTY = {
    "easy": (_PLUS5, _U7),
    "medium": (_PLUS5, _U7, _HOLLOW8),
    "hard": (_U7, _HOLLOW8),
    None: (_PLUS5, _U7, _HOLLOW8),
}
_ASYMMETRIC_BY_DIFFICULTY = {
    "easy": (_L3, _J4),
    "medium": (_L3, _J4, _STAIR4, _P5),
    "hard": (_J4, _STAIR4, _P5),
    None: (_L3, _J4, _STAIR4, _P5),
}

# Row-major roles for sample_index % 4. T = selected symmetric component,
# C = later same-color symmetric competitor, S = later singleton symmetric
# distractor of a different color, and A/B = asymmetric distractors.
_PROFILE_ROLES = (
    ("A", "T", "B"),
    ("T", "A", "S", "C", "B"),
    ("A", "T", "S", "B", "C"),
    ("A", "T", "B"),
)


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise ValueError("seed must be a Python int")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative Python int")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, lo, hi in (("grid_h", 7, 14), ("grid_w", 9, 16)):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be a Python int in {lo}..{hi}")


def _draw_dimension(ctx, overrides, name, lo, hi, scheduled):
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    if scheduled is not None:
        return ctx.draw_int_strict(name, scheduled, scheduled)
    return ctx.draw_int_strict(name, lo, hi)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _shape_variant(shape, rng):
    cells = tuple(shape)
    height = max(r for r, _ in cells) + 1
    width = max(c for _, c in cells) + 1
    if rng.choice((False, True)):
        cells = tuple((height - 1 - r, c) for r, c in cells)
    if rng.choice((False, True)):
        cells = tuple((r, width - 1 - c) for r, c in cells)
    return _normalize(cells)


def _slots(height, width, count):
    if count == 3:
        return (
            (0, 0),
            (0, width - 3),
            (height - 3, width - 3),
        )
    if count == 5:
        # The center role is always the singleton S. At the minimum 7x9
        # dimensions it remains at least Manhattan distance 2 from every
        # corner box, so no components merge accidentally.
        return (
            (0, 0),
            (0, width - 3),
            (height // 2, width // 2),
            (height - 3, 0),
            (height - 3, width - 3),
        )
    raise ValueError("component count must be 3 or 5")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    roles = _PROFILE_ROLES[sample_index % 4]
    canonical_anchor = len(roles) == 3
    height = _draw_dimension(
        ctx, overrides, "grid_h", 7, 14, 11 if canonical_anchor else None
    )
    width = _draw_dimension(
        ctx, overrides, "grid_w", 9, 16, 11 if canonical_anchor else None
    )
    rng = ctx.draw_rng("lesson")

    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 4)
    target_color, asym_a_color, asym_b_color, singleton_color = palette
    small = _shape_variant(rng.choice(_SMALL_BY_DIFFICULTY[difficulty]), rng)
    large = _shape_variant(rng.choice(_LARGE_BY_DIFFICULTY[difficulty]), rng)
    asym_a = _shape_variant(rng.choice(_ASYMMETRIC_BY_DIFFICULTY[difficulty]), rng)
    asym_b = _shape_variant(rng.choice(_ASYMMETRIC_BY_DIFFICULTY[difficulty]), rng)

    if sample_index % 2 == 0:
        target_shape, competitor_shape = small, large
    else:
        target_shape, competitor_shape = large, small

    role_to_shape_color = {
        "T": (target_shape, target_color),
        "C": (competitor_shape, target_color),
        "A": (asym_a, asym_a_color),
        "B": (asym_b, asym_b_color),
        "S": (_SINGLETON, singleton_color),
    }
    grid = full_grid(height, width, 0)
    for (top, left), role in zip(_slots(height, width, len(roles)), roles):
        shape, color = role_to_shape_color[role]
        paint_at(grid, top, left, shape, color)

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid ordered-component lesson: " + "; ".join(errors))
    return grid


def _authority_objects(grid):
    """Return monochrome 4-connected components in Racket row-major order."""
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbor_row = current_row + delta_row
                    neighbor_col = current_col + delta_col
                    neighbor = (neighbor_row, neighbor_col)
                    if (
                        0 <= neighbor_row < height
                        and 0 <= neighbor_col < width
                        and neighbor not in seen
                        and grid[neighbor_row][neighbor_col] == color
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            components.append(
                {
                    "color": color,
                    "cells": tuple(cells),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return components


def _object_crop(grid, obj):
    min_row, min_col, max_row, max_col = obj["bbox"]
    return [
        list(source[min_col:max_col + 1])
        for source in grid[min_row:max_row + 1]
    ]


def _binary_lr_symmetric(grid):
    binary = [[0 if value == 0 else 1 for value in row] for row in grid]
    return all(row == row[::-1] for row in binary)


def _analyze_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"], None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must be nonempty and rectangular"], None
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"], None
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid cells must be integer ARC colors 0..9"], None

    height = len(grid)
    errors = []
    if not 7 <= height <= 14:
        errors.append(f"grid height {height} outside 7..14")
    if not 9 <= width <= 16:
        errors.append(f"grid width {width} outside 9..16")

    components = _authority_objects(grid)
    if len(components) not in (3, 5):
        errors.append(f"expected 3 or 5 nonzero objects; found {len(components)}")
    colors = {obj["color"] for obj in components}
    if len(colors) < 2:
        errors.append(f"expected at least 2 nonzero colors; found {len(colors)}")

    infos = []
    for obj in components:
        crop = _object_crop(grid, obj)
        info = dict(obj)
        info["crop"] = crop
        info["lr_symmetric"] = _binary_lr_symmetric(crop)
        info["size"] = len(obj["cells"])
        infos.append(info)

    symmetric = [index for index, obj in enumerate(infos) if obj["lr_symmetric"]]
    asymmetric = [index for index, obj in enumerate(infos) if not obj["lr_symmetric"]]
    if not symmetric:
        errors.append("expected at least one LR-symmetric object")
    if not asymmetric:
        errors.append("expected at least one LR-asymmetric object")
    if symmetric:
        target = symmetric[0]
        if target == len(infos) - 1:
            errors.append("first LR-symmetric object must be followed by a distractor")
        if not any(index > target for index in asymmetric):
            errors.append("expected an LR-asymmetric distractor after the selected object")
        if target == 0 and not any(index > target for index in symmetric):
            errors.append("a first-position target needs a later LR-symmetric competitor")

    return errors, {
        "height": height,
        "width": width,
        "objects": infos,
        "target_index": symmetric[0] if symmetric else None,
    }


def rule_mirror(grid):
    """Independent Python mirror of the pinned Racket authority."""
    for obj in _authority_objects(grid):
        crop = _object_crop(grid, obj)
        if _binary_lr_symmetric(crop):
            return [[0 if value == 0 else 8 for value in row] for row in crop]
    return [[0]]


def self_check(grid, *, difficulty=None, meta=None):
    errors, _ = _analyze_grid(grid)
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    errors, analysis = _analyze_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {"grid_h": analysis["height"], "grid_w": analysis["width"]}
