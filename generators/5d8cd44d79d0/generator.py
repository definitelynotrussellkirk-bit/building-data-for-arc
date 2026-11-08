"""Generator for ARC task e21a174a / 5d8cd44d79d0.

The input contains monochromatic 8-connected objects in contiguous,
non-overlapping horizontal bands.  Reverse the top-to-bottom object order,
packing the same bounding-box heights into the original occupied span while
preserving every object's colour, internal pattern, and columns.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5d8cd44d79d0"
TASK_ID = "5d8cd44d79d0"
VERSION = "3.0.0"
RULE_HASH = "83de4fc7885e"

SUMMARY = (
    "A zero-background grid contains either three or five differently coloured "
    "8-connected objects. Each object occupies its own horizontal row band; "
    "the bands touch without blank rows and leave a blank border above and "
    "below. Reverse the objects' vertical order, packing their unchanged "
    "bounding-box heights into the same occupied span. Preserve each object's "
    "colour, internal pattern, and absolute columns."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0 with at least one blank row above and below the stack",
    "there are 3 or 5 distinct-colour 8-connected objects",
    "each colour forms exactly one object",
    "object row spans are disjoint and consecutive with no blank row between bands",
    "objects have different normalized shapes and mixed heights",
]

AXES = {
    "profile": {
        "type": "str",
        "default": "difficulty-weighted canonical profile",
        "valid": "compact|wide|large",
    },
    "shape_variant": {
        "type": "int",
        "default": "keyed 0..3",
        "valid": "0..3",
    },
    "column_layout": {
        "type": "str",
        "default": "keyed",
        "valid": "left|right|staggered",
    },
    "palette_variant": {
        "type": "int",
        "default": "keyed 0..3",
        "valid": "0..3",
    },
    "color_pattern": {
        "type": "str",
        "default": "keyed non-monotone order",
        "valid": "rotate|zigzag|swap_pairs",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_PROFILE_SPECS = {
    "compact": (7, 7, 3),
    "wide": (13, 10, 5),
    "large": (13, 13, 5),
}

_PROFILE_CHOICES = {
    None: ("compact", "wide", "large"),
    "easy": ("compact", "compact", "compact", "wide", "large"),
    "medium": ("compact", "wide", "wide", "large", "large"),
    "hard": ("compact", "wide", "large", "large", "large"),
}

# Each variant's first three heights sum to five (the 7x7 occupied span), and
# all five heights sum to eleven (the 13-row occupied span).  Every set contains
# a vertically asymmetric object, distinct normalized shapes, and widths below
# the compact profile's full inner width so left/right layouts stay observable.
_SHAPE_ROWS = {
    0: (
        ("1111",),
        ("111", "010"),
        ("1011", "0110"),
        ("111111", "111111", "111100"),
        ("001100", "011110", "110011"),
    ),
    1: (
        ("1110", "0011"),
        ("1111",),
        ("011", "110"),
        ("1111111", "1111110", "1110000"),
        ("101010", "011110", "001100"),
    ),
    2: (
        ("1101", "0110"),
        ("111", "100"),
        ("1111",),
        ("1111111", "0111111", "0001110"),
        ("001110", "011011", "110001"),
    ),
    3: (
        ("111",),
        ("1011", "1110"),
        ("1100", "0111"),
        ("11111111", "11111100", "11000000"),
        ("111000", "011110", "000111"),
    ),
}

_PALETTES = {
    3: (
        (1, 2, 3),
        (4, 5, 6),
        (2, 7, 9),
        (1, 4, 8),
    ),
    5: (
        (1, 2, 3, 4, 5),
        (2, 3, 4, 6, 8),
        (1, 3, 5, 7, 9),
        (2, 4, 5, 6, 8),
    ),
}

_PATTERN_INDICES = {
    3: {
        "rotate": (1, 2, 0),
        "zigzag": (0, 2, 1),
        "swap_pairs": (1, 0, 2),
    },
    5: {
        "rotate": (1, 2, 3, 4, 0),
        "zigzag": (0, 4, 1, 3, 2),
        "swap_pairs": (1, 0, 3, 2, 4),
    },
}

_DIR8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if not (dr == 0 and dc == 0)
)


def _cells(rows: Iterable[str]) -> tuple[tuple[int, int], ...]:
    return tuple(
        (row, col)
        for row, text in enumerate(rows)
        for col, value in enumerate(text)
        if value == "1"
    )


_SHAPE_SETS = {
    variant: tuple(_cells(rows) for rows in shape_rows)
    for variant, shape_rows in _SHAPE_ROWS.items()
}


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _shape_height(shape: Iterable[tuple[int, int]]) -> int:
    return max(row for row, _ in shape) + 1


def _shape_width(shape: Iterable[tuple[int, int]]) -> int:
    return max(col for _, col in shape) + 1


def _ordered_palette(
    palette: tuple[int, ...], pattern: str
) -> tuple[int, ...]:
    indices = _PATTERN_INDICES[len(palette)][pattern]
    return tuple(palette[index] for index in indices)


def _components_for_color(
    grid: list[list[int]], color: int
) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for drow, dcol in _DIR8:
                neighbor = row + drow, col + dcol
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a non-empty list of rows"]}
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular and non-empty"]}
    height = len(grid)
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid values must be integer ARC colours 0..9")

    colors = sorted({value for row in grid for value in row if value != 0})
    if len(colors) < 2:
        errors.append("at least two non-zero objects are required")

    bands: list[dict[str, Any]] = []
    for color in colors:
        components = _components_for_color(grid, color)
        if len(components) != 1:
            errors.append(
                f"colour {color} must form exactly one 8-connected object; "
                f"found {len(components)}"
            )
        for component in components:
            rows = [row for row, _ in component]
            cols = [col for _, col in component]
            bands.append(
                {
                    "color": color,
                    "cells": component,
                    "top": min(rows),
                    "bottom": max(rows),
                    "left": min(cols),
                    "right": max(cols),
                    "height": max(rows) - min(rows) + 1,
                    "width": max(cols) - min(cols) + 1,
                    "signature": _normalize(component),
                }
            )

    bands.sort(key=lambda obj: (obj["top"], obj["left"], obj["color"]))
    if bands:
        if bands[0]["top"] < 1:
            errors.append("the object stack must leave a blank row above")
        if bands[-1]["bottom"] > height - 2:
            errors.append("the object stack must leave a blank row below")
        for previous, current in zip(bands, bands[1:]):
            if current["top"] <= previous["bottom"]:
                errors.append(
                    "object row spans overlap: "
                    f"{(previous['top'], previous['bottom'])} then "
                    f"{(current['top'], current['bottom'])}"
                )
            elif current["top"] != previous["bottom"] + 1:
                errors.append(
                    "object bands must be consecutive without a blank row: "
                    f"{(previous['top'], previous['bottom'])} then "
                    f"{(current['top'], current['bottom'])}"
                )

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "colors": colors,
        "objects": bands,
        "first_top": bands[0]["top"] if bands else None,
        "last_bottom": bands[-1]["bottom"] if bands else None,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed stack grammars while accepting every canonical input."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if len(analysis["objects"]) > 9:
        errors.append("at most nine distinct-colour objects are supported")
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as "
                f"{observed.get(name)!r}"
            )
    return errors


def _profile_from_analysis(analysis: dict[str, Any]) -> str | None:
    key = (
        analysis["height"],
        analysis["width"],
        len(analysis["objects"]),
    )
    for name, spec in _PROFILE_SPECS.items():
        if key == spec:
            return name
    return None


def _column_layout(analysis: dict[str, Any]) -> str | None:
    bands = analysis["objects"]
    width = analysis["width"]
    left_positions = [obj["left"] for obj in bands]
    right_positions = [width - 1 - obj["width"] for obj in bands]
    if all(left == 1 for left in left_positions):
        return "left"
    if all(
        obj["right"] == width - 2
        for obj in bands
    ):
        return "right"
    expected = [1 if index % 2 == 0 else right_positions[index]
                for index in range(len(bands))]
    if left_positions == expected:
        return "staggered"
    return None


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact semantic axis from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    profile = _profile_from_analysis(analysis)
    if profile is None:
        return {}
    count = len(analysis["objects"])
    signatures = tuple(obj["signature"] for obj in analysis["objects"])
    shape_variant = next(
        (
            variant
            for variant, shapes in _SHAPE_SETS.items()
            if signatures == tuple(_normalize(shape) for shape in shapes[:count])
        ),
        None,
    )
    palette = tuple(sorted(analysis["colors"]))
    palette_variant = next(
        (
            variant
            for variant, candidate in enumerate(_PALETTES[count])
            if palette == candidate
        ),
        None,
    )
    color_sequence = tuple(obj["color"] for obj in analysis["objects"])
    color_pattern = next(
        (
            name
            for name in _PATTERN_INDICES[count]
            if color_sequence == _ordered_palette(palette, name)
        ),
        None,
    )
    return {
        "profile": profile,
        "shape_variant": shape_variant,
        "column_layout": _column_layout(analysis),
        "palette_variant": palette_variant,
        "color_pattern": color_pattern,
    }


def rule_mirror(grid):
    """Independent Python mirror used for tests; Racket remains authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid stacked-object scene: " + "; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    current_row = analysis["first_top"]
    for obj in reversed(analysis["objects"]):
        offset = current_row - obj["top"]
        for row, col in obj["cells"]:
            output[row + offset][col] = obj["color"]
        current_row += obj["height"]
    return output


def strict_canonical_like(grid) -> list[str]:
    """Task-linked lawful-manifold predicate used by the semantic gate."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    analysis = _analysis(grid)
    profile = _profile_from_analysis(analysis)
    if profile is None:
        reasons.append(
            "dimensions/object count are outside canonical profiles "
            "(7x7x3, 13x10x5, 13x13x5)"
        )
    if analysis["first_top"] != 1 or analysis["last_bottom"] != analysis["height"] - 2:
        reasons.append("canonical stacks occupy every row between one-row borders")
    if len(analysis["colors"]) != len(analysis["objects"]):
        reasons.append("canonical objects must have distinct colours")
    if len({obj["signature"] for obj in analysis["objects"]}) < 2:
        reasons.append("at least two distinct object shapes are required")
    if len({obj["height"] for obj in analysis["objects"]}) < 2:
        reasons.append("at least two object heights are required")
    return reasons


def _place_objects(
    grid: list[list[int]],
    ordered_objects: list[dict[str, Any]],
    *,
    transform=None,
    center: bool = False,
) -> list[list[int]]:
    analysis = _analysis(grid)
    output = full_grid(analysis["height"], analysis["width"], 0)
    current_row = analysis["first_top"]
    for obj in ordered_objects:
        cells = obj["signature"]
        if transform is not None:
            cells = transform(cells)
        shape_height = max(row for row, _ in cells) + 1
        shape_width = max(col for _, col in cells) + 1
        left = (analysis["width"] - shape_width) // 2 if center else obj["left"]
        for row, col in cells:
            output[current_row + row][left + col] = obj["color"]
        current_row += shape_height
    return output


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_reverse_colors_in_place(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    output = [list(row) for row in grid]
    colors = [obj["color"] for obj in analysis["objects"]][::-1]
    for obj, color in zip(analysis["objects"], colors):
        for row, col in obj["cells"]:
            output[row][col] = color
    return output


def _rival_flip_occupied_span(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    output = [list(row) for row in grid]
    top, bottom = analysis["first_top"], analysis["last_bottom"]
    output[top:bottom + 1] = reversed(output[top:bottom + 1])
    return output


def _rival_sort_objects_ascending(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    return _place_objects(
        grid,
        sorted(analysis["objects"], key=lambda obj: obj["color"]),
    )


def _rival_sort_objects_descending(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    return _place_objects(
        grid,
        sorted(analysis["objects"], key=lambda obj: obj["color"], reverse=True),
    )


def _rival_center_reversed_objects(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    return _place_objects(grid, list(reversed(analysis["objects"])), center=True)


def _flip_shape_vertically(
    cells: Iterable[tuple[int, int]],
) -> tuple[tuple[int, int], ...]:
    normalized = _normalize(cells)
    height = max(row for row, _ in normalized) + 1
    return _normalize((height - 1 - row, col) for row, col in normalized)


def _rival_reverse_and_flip_each_object(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    return _place_objects(
        grid,
        list(reversed(analysis["objects"])),
        transform=_flip_shape_vertically,
    )


SEMANTIC_RIVALS = {
    "identity": _rival_identity,
    "reverse_colors_in_place": _rival_reverse_colors_in_place,
    "flip_entire_occupied_span": _rival_flip_occupied_span,
    "sort_objects_ascending": _rival_sort_objects_ascending,
    "sort_objects_descending": _rival_sort_objects_descending,
    "center_reversed_objects": _rival_center_reversed_objects,
    "reverse_and_flip_each_object": _rival_reverse_and_flip_each_object,
}


def _rival_differs(grid, name: str) -> bool:
    expected = rule_mirror(grid)
    return SEMANTIC_RIVALS[name](grid) != expected


def _witness_profile(grid, profile: str) -> bool:
    observed = observe_overrides(grid)
    return observed.get("profile") == profile and _rival_differs(grid, "identity")


def _witness_shape_identity(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and len({obj["signature"] for obj in analysis["objects"]})
        == len(analysis["objects"])
        and _rival_differs(grid, "reverse_colors_in_place")
    )


def _witness_vertical_asymmetry(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and any(
            obj["signature"] != _flip_shape_vertically(obj["signature"])
            for obj in analysis["objects"]
        )
        and _rival_differs(grid, "flip_entire_occupied_span")
        and _rival_differs(grid, "reverse_and_flip_each_object")
    )


def _witness_nonmonotone_colors(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    colors = [obj["color"] for obj in analysis["objects"]]
    return (
        colors != sorted(colors)
        and colors != sorted(colors, reverse=True)
        and _rival_differs(grid, "sort_objects_ascending")
        and _rival_differs(grid, "sort_objects_descending")
    )


def _witness_columns_preserved(grid) -> bool:
    observed = observe_overrides(grid)
    return (
        observed.get("column_layout") in {"left", "right", "staggered"}
        and _rival_differs(grid, "center_reversed_objects")
    )


SEMANTIC_WITNESSES = {
    "compact_three_object_profile": lambda grid: _witness_profile(grid, "compact"),
    "wide_five_object_profile": lambda grid: _witness_profile(grid, "wide"),
    "large_five_object_profile": lambda grid: _witness_profile(grid, "large"),
    "distinct_shapes_refute_recolor_only": _witness_shape_identity,
    "vertical_asymmetry_refutes_row_flip": _witness_vertical_asymmetry,
    "nonmonotone_colors_refute_numeric_sort": _witness_nonmonotone_colors,
    "absolute_columns_refute_recentering": _witness_columns_preserved,
}

WITNESS_RIVALS = {
    "compact_three_object_profile": ["identity"],
    "wide_five_object_profile": ["identity"],
    "large_five_object_profile": ["identity"],
    "distinct_shapes_refute_recolor_only": ["reverse_colors_in_place"],
    "vertical_asymmetry_refutes_row_flip": [
        "flip_entire_occupied_span",
        "reverse_and_flip_each_object",
    ],
    "nonmonotone_colors_refute_numeric_sort": [
        "sort_objects_ascending",
        "sort_objects_descending",
    ],
    "absolute_columns_refute_recentering": ["center_reversed_objects"],
}

LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "reverse_colors_in_place": _rival_reverse_colors_in_place,
    "flip_entire_occupied_span": _rival_flip_occupied_span,
    "sort_objects_ascending": _rival_sort_objects_ascending,
    "sort_objects_descending": _rival_sort_objects_descending,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named wrong rule survives every demonstration."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    for index, pair in enumerate(demos):
        expected = rule_mirror(pair["input"])
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output does not match object-order reversal")
    query_input = query["input"]
    query_answer = rule_mirror(query_input)
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output does not match object-order reversal")
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"]
            for pair in demos
        )
        if survives and competitor(query_input) != query_answer:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("profile", _PROFILE_CHOICES[difficulty])
    shape_variant = ctx.draw_int("shape_variant", 0, 3)
    column_layout = ctx.draw_choice(
        "column_layout", ("left", "right", "staggered")
    )
    palette_variant = ctx.draw_int("palette_variant", 0, 3)
    color_pattern = ctx.draw_choice(
        "color_pattern", ("rotate", "zigzag", "swap_pairs")
    )

    height, width, count = _PROFILE_SPECS[profile]
    shapes = _SHAPE_SETS[shape_variant][:count]
    palette = _PALETTES[count][palette_variant]
    colors = _ordered_palette(palette, color_pattern)

    grid = full_grid(height, width, 0)
    current_row = 1
    for index, (shape, color) in enumerate(zip(shapes, colors)):
        shape_width = _shape_width(shape)
        if column_layout == "left":
            left = 1
        elif column_layout == "right":
            left = width - 1 - shape_width
        else:
            left = 1 if index % 2 == 0 else width - 1 - shape_width
        for row, col in shape:
            grid[current_row + row][left + col] = color
        current_row += _shape_height(shape)

    if current_row != height - 1:
        raise AssertionError(
            f"profile {profile}/{shape_variant} filled through row {current_row - 1}, "
            f"expected {height - 2}"
        )
    return grid
