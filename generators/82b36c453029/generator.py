"""Constructive generator for ARC task 82b36c453029.

The pinned Racket authority replaces every 4-connected nonzero object with one
same-colour cell at the floor midpoint of its tight bounding box.  The sampler
keeps canonical solid odd-sized rectangles in its support, then deliberately
adds four kinds of evidence the canonical examples omit:

* disconnected objects may share a colour;
* an asymmetric even-sized object separates bbox midpoint from cell centroid;
* the same object separates floor midpoint from upper/ceiling midpoint; and
* a ring has a bbox midpoint that is background in the input.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "82b36c453029"
TASK_ID = GENERATOR_ID
RULE_HASH = "b5f364e5c32b"
VERSION = "3.0.0"

SUMMARY = (
    "A 0-background grid contains three or four same-colour 4-connected "
    "objects.  Objects use two or three foreground colours, so disconnected "
    "objects can share a colour.  Replace each object—not each colour—with "
    "one same-colour cell at floor((r1+r2)/2, (c1+c2)/2) of its tight bounding "
    "box.  A three-profile schedule alternates canonical solid odd rectangles "
    "with repeated-colour asymmetric and hollow witnesses."
)

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 3
MIN_STRICT_FRAC = 0.20

INVARIANTS = [
    "rectangular 7..14 by 9..16 grid with background 0",
    "exactly 3..4 same-colour 4-connected objects",
    "each object is one of the declared canonical or witness shapes",
    "exactly 2..3 foreground colours; disconnected objects may repeat a colour",
    "all object bbox-center output positions are distinct",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "three-profile deterministic schedule with canonical anchors",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "three-profile deterministic schedule with canonical anchors",
        "valid": "9..16",
    },
    "components": {
        "type": "int",
        "default": "3 on canonical/witness-B profiles; 4 on witness-A",
        "valid": "3..4",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "3 on canonical profile; 2 on witness profiles",
        "valid": "2..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[tuple[str, ...]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = ("canonical", "witness_a", "witness_b")
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_CANONICAL_DIMS = ((9, 11), (8, 10), (10, 12), (7, 9), (9, 10))
_HEIGHT_CYCLES = {
    "easy": (7, 8, 9, 10, 11, 12, 13, 14),
    "medium": (9, 11, 13, 14, 12, 10, 8, 7),
    "hard": (14, 13, 12, 11, 10, 9, 8, 7),
}
_WIDTH_CYCLES = {
    "easy": (9, 10, 11, 12, 13, 14, 15, 16),
    "medium": (11, 13, 15, 16, 14, 12, 10, 9),
    "hard": (16, 15, 14, 13, 12, 11, 10, 9),
}

Shape = tuple[tuple[int, int], ...]


def _solid(height: int, width: int) -> Shape:
    return tuple((row, column) for row in range(height) for column in range(width))


# These are exactly the solid odd-sized rectangle profiles seen canonically.
_CANONICAL_SOLIDS: tuple[Shape, ...] = (
    _solid(3, 3),
    _solid(1, 3),
    _solid(3, 1),
    _solid(1, 5),
    _solid(5, 1),
)
_COMPACT_CANONICAL_SOLIDS: tuple[Shape, ...] = _CANONICAL_SOLIDS[:3]

# Bbox floor midpoint=(0,1); rounded cell centroid=(0,2); upper midpoint=(1,2).
_ASYMMETRIC_WITNESS: Shape = (
    (0, 0),
    (0, 1),
    (0, 2),
    (0, 3),
    (1, 3),
)

# Bbox midpoint=(1,1), but that cell is background in the input.
_HOLLOW_CENTER_WITNESS: Shape = (
    (0, 0),
    (0, 1),
    (0, 2),
    (1, 0),
    (1, 2),
    (2, 0),
    (2, 1),
    (2, 2),
)

_PLUS_SHAPE: Shape = (
    (0, 1),
    (1, 0),
    (1, 1),
    (1, 2),
    (2, 1),
)

_ALLOWED_SHAPES = frozenset(
    _CANONICAL_SOLIDS + (_ASYMMETRIC_WITNESS, _HOLLOW_CENTER_WITNESS, _PLUS_SHAPE)
)
_CANONICAL_BBOX_SHAPES = {(3, 3), (1, 3), (3, 1), (1, 5), (5, 1)}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the finite semantic profile for a production sample."""
    del seed
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_controls(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    bounds = {
        "grid_h": (7, 14),
        "grid_w": (9, 16),
        "components": (3, 4),
        "n_distinct_colors": (2, 3),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool or a coercible value)")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside {lo}..{hi}")


def _scheduled_int(ctx, overrides, name: str, scheduled: int, lo: int, hi: int) -> int:
    """Record an exact default while preserving the full strict override domain."""
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, scheduled, scheduled)


def _defaults(seed: int, sample_index: int, difficulty) -> tuple[int, int, int, int]:
    profile = schedule_profile(seed, sample_index, difficulty)
    band = difficulty or "medium"
    block = sample_index // LESSON_SCHEDULE_PERIOD
    if profile == "canonical":
        height, width = _CANONICAL_DIMS[(block + abs(seed)) % len(_CANONICAL_DIMS)]
        return height, width, 3, 3
    offset = (block + abs(seed)) % len(_HEIGHT_CYCLES[band])
    height = _HEIGHT_CYCLES[band][offset]
    width = _WIDTH_CYCLES[band][
        (offset * 3 + (1 if profile == "witness_b" else 0))
        % len(_WIDTH_CYCLES[band])
    ]
    if profile == "witness_a":
        return height, width, 4, 2
    return height, width, 3, 2


def _shape_size(shape: Shape) -> tuple[int, int]:
    return (
        max(row for row, _ in shape) + 1,
        max(column for _, column in shape) + 1,
    )


def _boxes_have_blank_line(
    first: tuple[int, int, int, int], second: tuple[int, int, int, int]
) -> bool:
    r1, c1, r2, c2 = first
    s1, d1, s2, d2 = second
    return r2 + 1 < s1 or s2 + 1 < r1 or c2 + 1 < d1 or d2 + 1 < c1


def _choose_anchors(height: int, width: int, shapes: list[Shape], rng) -> list[tuple[int, int]]:
    """Backtrack over actual shape boxes, retaining a blank row or column."""
    candidates: list[list[tuple[int, int, tuple[int, int, int, int]]]] = []
    for shape in shapes:
        shape_h, shape_w = _shape_size(shape)
        choices = [
            (row, column, (row, column, row + shape_h - 1, column + shape_w - 1))
            for row in range(height - shape_h + 1)
            for column in range(width - shape_w + 1)
        ]
        rng.shuffle(choices)
        candidates.append(choices)

    # Place the most spatially restrictive shapes first, then restore original order.
    order = sorted(
        range(len(shapes)),
        key=lambda index: (_shape_size(shapes[index])[0] * _shape_size(shapes[index])[1]),
        reverse=True,
    )
    selected: dict[int, tuple[int, int]] = {}
    boxes: list[tuple[int, int, int, int]] = []

    def search(depth: int) -> bool:
        if depth == len(order):
            return True
        shape_index = order[depth]
        for row, column, box in candidates[shape_index]:
            if all(_boxes_have_blank_line(box, prior) for prior in boxes):
                selected[shape_index] = (row, column)
                boxes.append(box)
                if search(depth + 1):
                    return True
                boxes.pop()
                del selected[shape_index]
        return False

    if not search(0):
        raise RuntimeError(
            f"could not place {len(shapes)} isolated object boxes in {height}x{width}"
        )
    return [selected[index] for index in range(len(shapes))]


def _canonical_shapes(count: int, rng, *, compact: bool = False) -> list[Shape]:
    pool = list(_COMPACT_CANONICAL_SOLIDS if compact else _CANONICAL_SOLIDS)
    rng.shuffle(pool)
    return [pool[index % len(pool)] for index in range(count)]


def _shape_schedule(profile: str, count: int, rng) -> list[Shape]:
    if profile == "canonical":
        return _canonical_shapes(count, rng)
    # Both witness profiles contain every decisive geometric witness.  Thus any
    # three demos left after holding one query out of four consecutive samples
    # still contain a surviving witness profile.
    shapes = [_ASYMMETRIC_WITNESS, _HOLLOW_CENTER_WITNESS, _PLUS_SHAPE]
    while len(shapes) < count:
        shapes.append(_PLUS_SHAPE)
    return shapes[:count]


def _color_schedule(count: int, distinct: int, rng) -> list[int]:
    palette = rng.sample(list(range(1, 10)), distinct)
    colors = list(palette)
    colors.extend(palette[index % distinct] for index in range(count - distinct))
    rng.shuffle(colors)
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct one lawful input with exact, observable public controls."""
    _validate_controls(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w, default_components, default_colors = _defaults(
        seed, sample_index, difficulty
    )
    height = _scheduled_int(ctx, overrides, "grid_h", default_h, 7, 14)
    width = _scheduled_int(ctx, overrides, "grid_w", default_w, 9, 16)
    count = _scheduled_int(ctx, overrides, "components", default_components, 3, 4)
    distinct = _scheduled_int(
        ctx, overrides, "n_distinct_colors", default_colors, 2, 3
    )

    profile = schedule_profile(seed, sample_index, difficulty)
    shape_rng = ctx.draw_rng("shapes")
    shapes = _shape_schedule(profile, count, shape_rng)
    placement_rng = ctx.draw_rng("placements")
    try:
        anchors = _choose_anchors(height, width, shapes, placement_rng)
    except RuntimeError:
        if profile != "canonical":
            raise
        # Exact minimum-size overrides can make a random pair of 1x5/5x1
        # shapes needlessly awkward.  Compact canonical shapes preserve the
        # true canonical manifold and guarantee constructive support.
        shapes = _canonical_shapes(count, shape_rng, compact=True)
        anchors = _choose_anchors(height, width, shapes, placement_rng)
    colors = _color_schedule(count, distinct, ctx.draw_rng("colors"))

    grid = full_grid(height, width, 0)
    for (top, left), shape, color in zip(anchors, shapes, colors):
        for drow, dcolumn in shape:
            row, column = top + drow, left + dcolumn
            if grid[row][column] != 0:
                raise RuntimeError("constructive placement overlap")
            grid[row][column] = color
    return grid


def _basic_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _components(grid) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == 0 or (row, column) in seen:
                continue
            stack = [(row, column)]
            seen.add((row, column))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                cr, cc = current
                for drow, dcolumn in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + drow, cc + dcolumn
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            columns = [c for _, c in cells]
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "bbox": (min(rows), min(columns), max(rows), max(columns)),
                }
            )
    return sorted(result, key=lambda item: (item["bbox"][0], item["bbox"][1]))


def _normalized_shape(component: dict[str, Any]) -> Shape:
    r1, c1, _, _ = component["bbox"]
    return tuple(sorted((row - r1, column - c1) for row, column in component["cells"]))


def _bbox_center(component: dict[str, Any]) -> tuple[int, int]:
    r1, c1, r2, c2 = component["bbox"]
    return (r1 + r2) // 2, (c1 + c2) // 2


def _nearest_centroid(component: dict[str, Any]) -> tuple[int, int]:
    cells = component["cells"]
    count = len(cells)
    return (
        (2 * sum(row for row, _ in cells) + count) // (2 * count),
        (2 * sum(column for _, column in cells) + count) // (2 * count),
    )


def _upper_center(component: dict[str, Any]) -> tuple[int, int]:
    r1, c1, r2, c2 = component["bbox"]
    return (r1 + r2 + 1) // 2, (c1 + c2 + 1) // 2


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject structural impostors while accepting canonical and generated inputs."""
    del difficulty, meta
    errors = _basic_grid_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not (7 <= height <= 14 and 9 <= width <= 16):
        errors.append(f"grid shape {height}x{width} outside 7..14 by 9..16")
    components = _components(grid)
    if not 3 <= len(components) <= 4:
        errors.append(f"expected 3..4 objects, found {len(components)}")
    distinct = len({component["color"] for component in components})
    if not 2 <= distinct <= 3:
        errors.append(f"expected 2..3 foreground colors, found {distinct}")
    centers: list[tuple[int, int]] = []
    for index, component in enumerate(components):
        normalized = _normalized_shape(component)
        if normalized not in _ALLOWED_SHAPES:
            errors.append(f"object {index} has an undeclared shape")
        centers.append(_bbox_center(component))
    if len(set(centers)) != len(centers):
        errors.append("two objects share the same bbox-center output cell")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover each public exact axis from a generated grid."""
    components = _components(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "components": len(components),
        "n_distinct_colors": len({component["color"] for component in components}),
    }


def strict_canonical_like(grid) -> list[str]:
    """Recognize the five canonical solid-rectangle input profiles."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    profile = (len(grid), len(grid[0]))
    if profile not in set(_CANONICAL_DIMS):
        reasons.append(f"grid dimensions {profile} are outside canonical profiles")
    components = _components(grid)
    if len(components) != 3:
        reasons.append(f"canonical inputs contain 3 objects, found {len(components)}")
    if len({component["color"] for component in components}) != 3:
        reasons.append("canonical inputs use a distinct color for every object")
    for index, component in enumerate(components):
        r1, c1, r2, c2 = component["bbox"]
        bbox_shape = (r2 - r1 + 1, c2 - c1 + 1)
        expected_cells = (r2 - r1 + 1) * (c2 - c1 + 1)
        if bbox_shape not in _CANONICAL_BBOX_SHAPES:
            reasons.append(f"canonical object {index} bbox {bbox_shape} is unsupported")
        if len(component["cells"]) != expected_cells:
            reasons.append(f"canonical object {index} is not a solid rectangle")
    return reasons


def _blank_like(grid):
    return [[0 for _ in row] for row in grid]


def rule_mirror(grid):
    """Independent Python mirror of the pinned Racket object/bbox rule."""
    output = _blank_like(grid)
    for component in _components(grid):
        row, column = _bbox_center(component)
        output[row][column] = component["color"]
    return output


def _one_center_per_color(grid):
    output = _blank_like(grid)
    colors = sorted({value for row in grid for value in row if value != 0})
    for color in colors:
        cells = [
            (row, column)
            for row, values in enumerate(grid)
            for column, value in enumerate(values)
            if value == color
        ]
        rows = [row for row, _ in cells]
        columns = [column for _, column in cells]
        output[(min(rows) + max(rows)) // 2][(min(columns) + max(columns)) // 2] = color
    return output


def _nearest_cell_centroid(grid):
    output = _blank_like(grid)
    for component in _components(grid):
        row, column = _nearest_centroid(component)
        output[row][column] = component["color"]
    return output


def _upper_bbox_midpoint(grid):
    output = _blank_like(grid)
    for component in _components(grid):
        row, column = _upper_center(component)
        output[row][column] = component["color"]
    return output


def _occupied_center_only(grid):
    output = _blank_like(grid)
    for component in _components(grid):
        row, column = _bbox_center(component)
        if grid[row][column] == component["color"]:
            output[row][column] = component["color"]
    return output


def _has_repeated_color_objects(grid) -> bool:
    counts = Counter(component["color"] for component in _components(grid))
    return any(count > 1 for count in counts.values())


def _centroid_differs(grid) -> bool:
    return any(
        _nearest_centroid(component) != _bbox_center(component)
        for component in _components(grid)
    )


def _floor_midpoint_matters(grid) -> bool:
    return any(
        _upper_center(component) != _bbox_center(component)
        for component in _components(grid)
    )


def _bbox_center_is_background(grid) -> bool:
    return any(
        grid[row][column] != component["color"]
        for component in _components(grid)
        for row, column in [_bbox_center(component)]
    )


SEMANTIC_RIVALS = {
    "one_center_per_color": _one_center_per_color,
    "nearest_cell_centroid": _nearest_cell_centroid,
    "upper_bbox_midpoint": _upper_bbox_midpoint,
    "occupied_center_only": _occupied_center_only,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "repeated_color_objects": _has_repeated_color_objects,
    "centroid_differs": _centroid_differs,
    "floor_midpoint_matters": _floor_midpoint_matters,
    "bbox_center_is_background": _bbox_center_is_background,
}
WITNESS_RIVALS = {
    "repeated_color_objects": ("one_center_per_color",),
    "centroid_differs": ("nearest_cell_centroid",),
    "floor_midpoint_matters": ("upper_bbox_midpoint",),
    "bbox_center_is_background": ("occupied_center_only",),
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report declared shortcut ambiguity for one labeled lesson."""
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        try:
            expected = rule_mirror(deepcopy(pair["input"]))
        except Exception as exc:  # pragma: no cover - defensive contract report
            reasons.append(f"demo {index} is invalid: {type(exc).__name__}: {exc}")
            continue
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output does not match the bbox-center rule")
    try:
        query_answer = rule_mirror(deepcopy(query["input"]))
    except Exception as exc:  # pragma: no cover - defensive contract report
        reasons.append(f"query is invalid: {type(exc).__name__}: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output does not match the bbox-center rule")
    for name, rival in LESSON_COMPETITORS.items():
        survives = all(
            rival(deepcopy(pair["input"])) == pair.get("output") for pair in demos
        )
        if survives and rival(deepcopy(query["input"])) != query_answer:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons
