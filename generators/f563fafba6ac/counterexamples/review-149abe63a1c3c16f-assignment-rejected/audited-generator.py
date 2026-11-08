"""Generator for H19 / f563fafba6ac: sort objects by enclosed holes.

Each input contains three or four separated, monochromatic objects on color 0.
For every object the selected rule counts enclosed background regions inside its
bounding box, normalizes the object to the top-left, sorts by
``(hole_count, color)``, and packs the normalized objects left-to-right with one
background column between neighbours.

The curriculum deliberately includes three executable counterexamples on every
ordinary draw:

* color alone cannot order objects (low-hole objects receive high colors),
* input order cannot resolve equal-hole ties (equal-hole colors appear in
  descending reading order), and
* area cannot replace hole count (the zero-hole object is larger than a
  one-hole ring).
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f563fafba6ac"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "458549b829a3"

SUMMARY = (
    "Three or four separated monochromatic objects have 0, 1, or 2 enclosed "
    "holes. Normalize each object, sort by (hole_count, color), and pack the "
    "objects left-to-right with one zero column between neighbours. Ordinary "
    "draws explicitly refute color-only, stable-input-tie, and area-order "
    "shortcuts while retaining canonical 11x15 and 14x15 profiles."
)

INVARIANTS = [
    "background is 0 and all cells are integer ARC colors",
    "there are exactly 3 or 4 monochromatic 4-connected objects",
    "object colors are distinct and object bounding boxes have a one-cell halo",
    "objects span at least two enclosed-hole counts from 0, 1, and 2",
    "the packed result never exceeds the input height or width",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchors plus difficulty-aware values",
        "valid": "11..24",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchors plus difficulty-aware values",
        "valid": "15..28",
    },
    "n_objects": {
        "type": "int",
        "default": "3 easy / 3-4 medium-hard",
        "valid": "3..4",
    },
    "hole_counts": {
        "type": "list",
        "default": "[0,1,1] or [0,1,1,2]",
        "valid": "length n_objects; each 0..2; at least two distinct",
        "probe": "diagnostic",
    },
}

# This generator has no advertised texture axis.  Keeping these declarations
# explicit prevents a future reviewer from mistaking invalid examples for a
# supported ordinary domain.
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

_GRID_H_BOUNDS = (11, 24)
_GRID_W_BOUNDS = (15, 28)
_N_OBJECT_BOUNDS = (3, 4)
_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")


def _normalize(cells: set[tuple[int, int]] | list[tuple[int, int]]) -> set[tuple[int, int]]:
    points = set(cells)
    if not points:
        return set()
    row0 = min(row for row, _ in points)
    col0 = min(col for _, col in points)
    return {(row - row0, col - col0) for row, col in points}


def _shape_size(cells: set[tuple[int, int]] | list[tuple[int, int]]) -> tuple[int, int]:
    points = set(cells)
    if not points:
        return (0, 0)
    return (
        max(row for row, _ in points) + 1,
        max(col for _, col in points) + 1,
    )


def _solid_shape(variant: int) -> set[tuple[int, int]]:
    """Return a width-three, no-hole object with area greater than a 3x3 ring."""
    if variant % 3 == 0:
        return {(row, col) for row in range(3) for col in range(3)}
    if variant % 3 == 1:
        return {(row, col) for row in range(4) for col in range(3)}
    # Two missing border corners preserve connectivity and cannot form a hole.
    return {
        (row, col)
        for row in range(4)
        for col in range(3)
        if (row, col) not in {(0, 2), (3, 0)}
    }


def _ring_shape() -> set[tuple[int, int]]:
    return {
        (row, col)
        for row in range(3)
        for col in range(3)
        if (row, col) != (1, 1)
    }


def _two_hole_shape() -> set[tuple[int, int]]:
    # Two enclosed vertical regions (lengths two and three).  The 8x3 frame
    # contains 19 cells, matching the canonical task's largest object while
    # staying narrow enough for a nonexpanding four-object output on width 15.
    open_cells = {(1, 1), (2, 1), (4, 1), (5, 1), (6, 1)}
    return {
        (row, col)
        for row in range(8)
        for col in range(3)
        if (row, col) not in open_cells
    }


def _shape_for_holes(hole_count: int, variant: int) -> set[tuple[int, int]]:
    if hole_count == 0:
        return _solid_shape(variant)
    if hole_count == 1:
        return _ring_shape()
    if hole_count == 2:
        return _two_hole_shape()
    raise ValueError(f"unsupported hole count: {hole_count!r}")


def _rectangles_compatible(
    first: tuple[int, int, int, int],
    second: tuple[int, int, int, int],
) -> bool:
    """True when the two bboxes have at least one blank row or column."""
    row_a, col_a, height_a, width_a = first
    row_b, col_b, height_b, width_b = second
    return (
        row_a + height_a < row_b
        or row_b + height_b < row_a
        or col_a + width_a < col_b
        or col_b + width_b < col_a
    )


def _random_placements(shapes, height: int, width: int, rng):
    """Place all shape bboxes with a halo; return positions or ``None``."""
    order = sorted(
        range(len(shapes)),
        key=lambda index: _shape_size(shapes[index])[0] * _shape_size(shapes[index])[1],
        reverse=True,
    )
    for _attempt in range(120):
        placed: dict[int, tuple[int, int]] = {}
        rectangles: list[tuple[int, int, int, int]] = []
        attempt_order = list(order)
        # Preserve largest-first placement but vary equal-size objects.
        rng.shuffle(attempt_order)
        attempt_order.sort(
            key=lambda index: _shape_size(shapes[index])[0] * _shape_size(shapes[index])[1],
            reverse=True,
        )
        failed = False
        for index in attempt_order:
            shape_h, shape_w = _shape_size(shapes[index])
            candidates = [
                (row, col)
                for row in range(height - shape_h + 1)
                for col in range(width - shape_w + 1)
            ]
            rng.shuffle(candidates)
            chosen = None
            for row, col in candidates:
                rectangle = (row, col, shape_h, shape_w)
                if all(_rectangles_compatible(rectangle, other) for other in rectangles):
                    chosen = (row, col)
                    rectangles.append(rectangle)
                    placed[index] = chosen
                    break
            if chosen is None:
                failed = True
                break
        if not failed:
            return [placed[index] for index in range(len(shapes))]
    return None


def _fallback_placements(shapes, height: int, width: int):
    """Deterministic one-row fallback for the minimum 11x15 canvas."""
    sizes = [_shape_size(shape) for shape in shapes]
    required_width = sum(shape_w for _, shape_w in sizes) + len(sizes) - 1
    required_height = max(shape_h for shape_h, _ in sizes)
    if required_width > width or required_height > height:
        raise ValueError("requested grid is too small for the object grammar")
    positions: list[tuple[int, int]] = []
    cursor_col = 0
    for shape_h, shape_w in sizes:
        positions.append(((height - shape_h) // 2, cursor_col))
        cursor_col += shape_w + 1
    return positions


def _validate_hole_counts(value: Any, n_objects: int | None = None) -> list[int]:
    if type(value) is not list:
        raise TypeError("hole_counts override must be a list")
    if not 3 <= len(value) <= 4:
        raise ValueError("hole_counts must contain 3 or 4 entries")
    if n_objects is not None and len(value) != n_objects:
        raise ValueError("hole_counts length must equal n_objects")
    if any(type(item) is not int for item in value):
        raise TypeError("hole_counts entries must be integers (not bool)")
    if any(item not in (0, 1, 2) for item in value):
        raise ValueError("hole_counts entries must be in 0..2")
    if len(set(value)) < 2:
        raise ValueError("hole_counts must exercise at least two distinct counts")
    return list(value)


def _default_ranges(difficulty):
    if difficulty == "easy":
        return (11, 14), (15, 18), (3, 3)
    if difficulty == "hard":
        return (16, 24), (18, 28), (4, 4)
    if difficulty == "medium":
        return (13, 18), (16, 22), (3, 4)
    return _GRID_H_BOUNDS, _GRID_W_BOUNDS, _N_OBJECT_BOUNDS


def _canonical_anchor(sample_index: int, overrides: dict[str, Any]) -> bool:
    return not overrides and int(sample_index) % 4 == 0


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic task input and honor every declared override."""
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis(es): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    anchor = _canonical_anchor(sample_index, overrides)
    height_range, width_range, object_range = _default_ranges(difficulty)

    if "grid_h" in overrides and overrides["grid_h"] is not None:
        height = ctx.draw_int_strict("grid_h", *_GRID_H_BOUNDS)
    elif anchor:
        anchor_height = 11 if (int(seed) + int(sample_index)) % 2 == 0 else 14
        height = ctx.draw_int_strict("grid_h", anchor_height, anchor_height)
    else:
        height = ctx.draw_int_strict("grid_h", *height_range)

    if "grid_w" in overrides and overrides["grid_w"] is not None:
        width = ctx.draw_int_strict("grid_w", *_GRID_W_BOUNDS)
    elif anchor:
        width = ctx.draw_int_strict("grid_w", 15, 15)
    else:
        width = ctx.draw_int_strict("grid_w", *width_range)

    supplied_holes = overrides.get("hole_counts")
    if supplied_holes is not None:
        prechecked_holes = _validate_hole_counts(supplied_holes)
        inferred_n = len(prechecked_holes)
    else:
        prechecked_holes = None
        inferred_n = None

    if "n_objects" in overrides and overrides["n_objects"] is not None:
        n_objects = ctx.draw_int_strict("n_objects", *_N_OBJECT_BOUNDS)
        if inferred_n is not None and inferred_n != n_objects:
            raise ValueError("hole_counts length must equal n_objects")
    elif inferred_n is not None:
        n_objects = ctx.draw_int_strict("n_objects", inferred_n, inferred_n)
    elif anchor:
        n_objects = ctx.draw_int_strict("n_objects", 3, 3)
    else:
        n_objects = ctx.draw_int_strict("n_objects", *object_range)

    if prechecked_holes is not None:
        requested_holes = _validate_hole_counts(prechecked_holes, n_objects)
    else:
        requested_holes = [0, 1, 1] if n_objects == 3 else [0, 1, 1, 2]
    # A one-option keyed choice records provenance for this structured exact
    # axis while preserving list-valued overrides without coercion.
    hole_counts = list(ctx.draw_choice("hole_counts", [requested_holes]))

    shape_rng = ctx.draw_rng("shapes")
    shapes = [
        _shape_for_holes(hole_count, shape_rng.randrange(3))
        for hole_count in hole_counts
    ]

    layout_rng = ctx.draw_rng("layout")
    positions = _random_placements(shapes, height, width, layout_rng)
    if positions is None:
        positions = _fallback_placements(shapes, height, width)

    # Numeric color is the canonical tie-breaker, but it must not reveal the
    # primary hole order.  Assign descending sampled colors in hole/input order:
    # lower-hole objects therefore get higher colors, and equal-hole objects are
    # encountered in descending color order by a reading-order scan.
    palette_rng = ctx.draw_rng("palette")
    sampled_colors = sorted(palette_rng.sample(list(range(1, 10)), n_objects), reverse=True)
    reading_order = sorted(
        range(n_objects),
        key=lambda index: (hole_counts[index], positions[index][0], positions[index][1]),
    )
    colors: list[int | None] = [None] * n_objects
    for color, index in zip(sampled_colors, reading_order):
        colors[index] = color

    grid = full_grid(height, width, 0)
    for index, shape in enumerate(shapes):
        row0, col0 = positions[index]
        color = colors[index]
        assert color is not None
        for row, col in shape:
            grid[row0 + row][col0 + col] = color

    findings = self_check(grid)
    if findings:
        raise RuntimeError("generator produced an invalid grid: " + "; ".join(findings))
    return grid


def _grid_shape(grid: Any) -> tuple[int, int] | None:
    if type(grid) is not list or not grid:
        return None
    if any(type(row) is not list or not row for row in grid):
        return None
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None
    return (len(grid), width)


def _count_holes(normalized: set[tuple[int, int]], height: int, width: int) -> int:
    background = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in normalized
    }
    seen: set[tuple[int, int]] = set()
    holes = 0
    for start in background:
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        touches_edge = start[0] in (0, height - 1) or start[1] in (0, width - 1)
        while stack:
            row, col = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                point = (row + dr, col + dc)
                if point in background and point not in seen:
                    seen.add(point)
                    stack.append(point)
                    touches_edge = touches_edge or (
                        point[0] in (0, height - 1)
                        or point[1] in (0, width - 1)
                    )
        if not touches_edge:
            holes += 1
    return holes


def _objects(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            absolute: set[tuple[int, int]] = set()
            while stack:
                current = stack.pop()
                absolute.add(current)
                current_row, current_col = current
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    point = (current_row + dr, current_col + dc)
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and point not in seen
                        and grid[point[0]][point[1]] == color
                    ):
                        seen.add(point)
                        stack.append(point)
            row0 = min(r for r, _ in absolute)
            col0 = min(c for _, c in absolute)
            normalized = {(r - row0, c - col0) for r, c in absolute}
            shape_h, shape_w = _shape_size(normalized)
            components.append(
                {
                    "color": color,
                    "absolute": absolute,
                    "cells": normalized,
                    "row": row0,
                    "col": col0,
                    "height": shape_h,
                    "width": shape_w,
                    "area": len(normalized),
                    "holes": _count_holes(normalized, shape_h, shape_w),
                }
            )
    return components


def _pack(components: list[dict[str, Any]], key: Callable[[dict[str, Any]], Any]):
    if not components:
        raise ValueError("cannot pack an empty object list")
    ordered = sorted(components, key=key)
    height = max(obj["height"] for obj in ordered)
    width = sum(obj["width"] for obj in ordered) + len(ordered) - 1
    output = full_grid(height, width, 0)
    left = 0
    for obj in ordered:
        for row, col in obj["cells"]:
            output[row][left + col] = obj["color"]
        left += obj["width"] + 1
    return output


def self_check(grid) -> list[str]:
    """Return concise reasons when ``grid`` is outside the task grammar."""
    shape = _grid_shape(grid)
    if shape is None:
        return ["grid must be a non-empty rectangular list of non-empty rows"]
    height, width = shape
    reasons: list[str] = []
    if not (_GRID_H_BOUNDS[0] <= height <= _GRID_H_BOUNDS[1]):
        reasons.append(f"grid height {height} is outside 11..24")
    if not (_GRID_W_BOUNDS[0] <= width <= _GRID_W_BOUNDS[1]):
        reasons.append(f"grid width {width} is outside 15..28")

    bad_cell = next(
        (
            (row, col, value)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if type(value) is not int or not 0 <= value <= 9
        ),
        None,
    )
    if bad_cell is not None:
        row, col, value = bad_cell
        reasons.append(f"cell ({row},{col}) is not an integer ARC color: {value!r}")
        return reasons

    components = _objects(grid)
    if not 3 <= len(components) <= 4:
        reasons.append(f"expected 3 or 4 objects, found {len(components)}")
    colors = [obj["color"] for obj in components]
    if len(colors) != len(set(colors)):
        reasons.append("each nonzero color must form exactly one connected object")
    if any(obj["area"] < 4 for obj in components):
        reasons.append("every object must contain at least four cells")
    invalid_holes = [obj["holes"] for obj in components if obj["holes"] not in (0, 1, 2)]
    if invalid_holes:
        reasons.append(f"object hole counts must be in 0..2, found {invalid_holes}")
    hole_counts = {obj["holes"] for obj in components}
    if len(hole_counts) < 2:
        reasons.append("objects must exercise at least two distinct hole counts")

    for first_index, first in enumerate(components):
        first_rect = (first["row"], first["col"], first["height"], first["width"])
        for second in components[first_index + 1 :]:
            second_rect = (
                second["row"],
                second["col"],
                second["height"],
                second["width"],
            )
            if not _rectangles_compatible(first_rect, second_rect):
                reasons.append("object bounding boxes must have a one-cell halo")
                break
        if reasons and reasons[-1] == "object bounding boxes must have a one-cell halo":
            break

    if components:
        output_height = max(obj["height"] for obj in components)
        output_width = sum(obj["width"] for obj in components) + len(components) - 1
        if output_height > height or output_width > width:
            reasons.append(
                f"packed output {output_height}x{output_width} exceeds input {height}x{width}"
            )
    return reasons


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    findings = self_check(grid)
    if findings:
        raise ValueError("cannot observe invalid grid: " + "; ".join(findings))
    components = _objects(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_objects": len(components),
        "hole_counts": sorted(obj["holes"] for obj in components),
    }


def rule_mirror(grid):
    findings = self_check(grid)
    if findings:
        raise ValueError("input is outside the task grammar: " + "; ".join(findings))
    return _pack(_objects(grid), lambda obj: (obj["holes"], obj["color"]))


def _color_only(grid):
    return _pack(_objects(grid), lambda obj: obj["color"])


def _stable_input_ties(grid):
    return _pack(_objects(grid), lambda obj: (obj["holes"], obj["row"], obj["col"]))


def _area_then_color(grid):
    return _pack(_objects(grid), lambda obj: (obj["area"], obj["color"]))


def _differs(rival):
    def witness(grid):
        try:
            return rival(grid) != rule_mirror(grid)
        except (TypeError, ValueError, IndexError):
            return False

    return witness


SEMANTIC_RIVALS = {
    "color_only": _color_only,
    "stable_input_ties": _stable_input_ties,
    "area_then_color": _area_then_color,
}
SEMANTIC_WITNESSES = {
    "hole_priority": _differs(_color_only),
    "color_tiebreak": _differs(_stable_input_ties),
    "holes_not_area": _differs(_area_then_color),
}
WITNESS_RIVALS = {
    "hole_priority": ["color_only"],
    "color_tiebreak": ["stable_input_ties"],
    "holes_not_area": ["area_then_color"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "stable_input_ties": _stable_input_ties,
    "area_then_color": _area_then_color,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Validate a lesson and report rivals that its demonstrations leave alive."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]

    reasons: list[str] = []
    validated_demos = []
    for index, pair in enumerate(list(demos) + [query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} must contain input and output")
            continue
        findings = self_check(pair["input"])
        if findings:
            reasons.append(f"pair {index} is outside the grammar: {findings[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"pair {index} output disagrees with the selected rule")
            continue
        if index < len(demos):
            validated_demos.append(pair)
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(rival(pair["input"]) == pair["output"] for pair in validated_demos)
            if survives and rival(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not falsify rival: {name}")
        except Exception as exc:  # fail loud through a returned diagnostic
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
    return reasons
