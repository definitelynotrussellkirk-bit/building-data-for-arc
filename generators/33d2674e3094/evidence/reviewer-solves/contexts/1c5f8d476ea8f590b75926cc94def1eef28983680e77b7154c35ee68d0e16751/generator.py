"""Generator for ARC task 33d2674e3094: descending-area object gallery.

Every input contains exactly three disconnected monochrome objects on black.
The authoritative rule crops each object to its bounding box, sorts the crops by
*descending cell count* (not bounding-box area), breaks equal-area ties by the
object bounding box in ``(top, bottom, left, right)`` order, and packs the crops
left-to-right, top-aligned, with one black separator column.

The default four-example curriculum alternates equal-area and unequal-area
scenes.  Every three-demo query rotation therefore contains a tie witness.  The
tie witness is important because all public examples are also consistent with
the wrong shortcut "break equal-area ties by ascending color".
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "33d2674e3094"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "9f849a344655"

SUMMARY = (
    "Three disconnected monochrome objects appear on black. Crop each object "
    "to its bounding box, sort by descending cell area, break equal-area ties "
    "by top/bottom/left/right bounding-box order, then concatenate the crops "
    "left-to-right, top-aligned, with one black separator column. Scheduled "
    "tie scenes rule out color-based tie breaking; sparse shapes distinguish "
    "cell area from bounding-box area."
)

INVARIANTS = [
    "the canvas is one of the three public shape profiles",
    "there are exactly three disconnected monochrome 4-connected objects",
    "the three objects use distinct nonzero colors",
    "object cell areas follow one of the three public area patterns",
    "objects are separated and their bounding boxes do not overlap",
    "every four consecutive examples retain a tie witness under any query rotation",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

PROFILES = ("p8x13", "p9x12", "p10x11")
AREA_PATTERNS = ("tie_443", "distinct_653", "distinct_643")

_PROFILE_INFO = {
    "p8x13": (8, 13),
    "p9x12": (9, 12),
    "p10x11": (10, 11),
}
_PROFILE_BY_SHAPE = {shape: name for name, shape in _PROFILE_INFO.items()}
_AREA_SIZES = {
    "tie_443": (4, 4, 3),
    "distinct_653": (6, 5, 3),
    "distinct_643": (6, 4, 3),
}
_AREA_PATTERN_BY_SIZES = {sizes: name for name, sizes in _AREA_SIZES.items()}
_BAND_OFFSETS = {"easy": 0, "medium": 1, "hard": 2}

AXES = {
    "profile": {
        "type": "str",
        "default": "scheduled across all three public shape profiles",
        "valid": "p8x13|p9x12|p10x11",
        "doc": "Exact returned canvas shape.",
    },
    "area_pattern": {
        "type": "str",
        "default": "alternating tie and distinct public area patterns",
        "valid": "tie_443|distinct_653|distinct_643",
        "doc": "Descending multiset of the three object cell areas.",
    },
}
_ALLOWED_OVERRIDES = frozenset(AXES)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Relative 4-connected shapes.  Their deliberately different cell and bbox
# areas make the semantic rivals below observable in every generated scene.
_VERTICAL_3 = ((0, 0), (1, 0), (2, 0))
_SQUARE_4 = ((0, 0), (0, 1), (1, 0), (1, 1))
_T_4 = ((0, 0), (0, 1), (0, 2), (1, 1))
_PLUS_5 = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
_RECT_6 = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2))


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if isinstance(difficulty, str) and difficulty in _BAND_OFFSETS:
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Cycle through every public shape in every difficulty band."""
    del seed
    band = _band(difficulty)
    return PROFILES[(int(sample_index) + _BAND_OFFSETS[band]) % len(PROFILES)]


def schedule_area_pattern(seed: int, sample_index: int, difficulty=None) -> str:
    """Alternate tie scenes with both unequal-area public patterns."""
    del seed
    band = _band(difficulty)
    position = int(sample_index) + _BAND_OFFSETS[band]
    if position % 2 == 0:
        return "tie_443"
    return ("distinct_653", "distinct_643")[(position // 2) % 2]


def _validate_requested_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    if "profile" in overrides and overrides["profile"] is not None:
        value = overrides["profile"]
        if not isinstance(value, str) or value not in PROFILES:
            raise ValueError(f"unknown profile: {value!r}")
    if "area_pattern" in overrides and overrides["area_pattern"] is not None:
        value = overrides["area_pattern"]
        if not isinstance(value, str) or value not in AREA_PATTERNS:
            raise ValueError(f"unknown area_pattern: {value!r}")


def _paint(
    grid: list[list[int]],
    shape: Sequence[tuple[int, int]],
    top: int,
    left: int,
    color: int,
) -> None:
    for dr, dc in shape:
        row, col = top + dr, left + dc
        if not (0 <= row < len(grid) and 0 <= col < len(grid[0])):
            raise RuntimeError("constructive object placement escaped the canvas")
        if grid[row][col] != 0:
            raise RuntimeError("constructive object placement overlapped an object")
        grid[row][col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one exact-contract gallery-sorting input without retries."""
    _validate_requested_overrides(overrides)
    band = _band(difficulty)
    selected_profile = overrides.get("profile") or schedule_profile(
        seed, sample_index, band
    )
    selected_pattern = overrides.get("area_pattern") or schedule_area_pattern(
        seed, sample_index, band
    )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice("profile", [selected_profile])
    area_pattern = ctx.draw_choice("area_pattern", [selected_pattern])

    height, width = _PROFILE_INFO[profile]
    grid = full_grid(height, width, 0)
    top = ctx.draw_int("shared_top", 1, height - 4)
    horizontal_phase = ctx.draw_int("horizontal_phase", 0, width - 11)
    lane_lefts = (1 + horizontal_phase, 3 + horizontal_phase, 7 + horizontal_phase)

    # Numeric color rank is deliberately non-monotone in authority order.
    # Primary, secondary, small receive middle, low, high respectively, so
    # neither ascending nor descending color order reproduces the gallery.
    # On tie scenes, ascending color also reverses the two equal-area objects.
    low, middle, high = sorted(
        ctx.draw_distinct_colors("object_colors", n=3, exclude=(0,))
    )
    primary_color, secondary_color, small_color = middle, low, high
    small = (_VERTICAL_3, small_color, lane_lefts[0])

    if area_pattern == "tie_443":
        # Equal areas: bbox order chooses the compact square at lane 1, while
        # bbox area and ascending tie color both choose the T at lane 2.
        lane_objects = [
            small,
            (_SQUARE_4, primary_color, lane_lefts[1]),
            (_T_4, secondary_color, lane_lefts[2]),
        ]
    elif area_pattern == "distinct_653":
        # The 5-cell plus has bbox area 9, exceeding the 6-cell rectangle's 6.
        lane_objects = [
            small,
            (_RECT_6, primary_color, lane_lefts[1]),
            (_PLUS_5, secondary_color, lane_lefts[2]),
        ]
    else:  # distinct_643
        # Both non-small crops have bbox area 6.  Put the smaller T earlier so
        # bbox-area+bbox-order disagrees with descending cell area.
        lane_objects = [
            small,
            (_T_4, secondary_color, lane_lefts[1]),
            (_RECT_6, primary_color, lane_lefts[2]),
        ]

    for shape, color, left in lane_objects:
        _paint(grid, shape, top, left, color)

    errors = self_check(grid)
    if errors:
        raise RuntimeError("generator produced invalid grid: " + "; ".join(errors[:4]))
    return grid


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular with non-empty rows"]
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return ["grid values must be integer ARC colors in 0..9"]
    return []


def _objects(grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r0, c0 = current
                for dr, dc in _CARDINAL:
                    nr, nc = r0 + dr, c0 + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1 = min(r for r, _ in cells)
            r2 = max(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            c2 = max(c for _, c in cells)
            crop = [[0 for _ in range(c2 - c1 + 1)] for _ in range(r2 - r1 + 1)]
            for r, c in cells:
                crop[r - r1][c - c1] = color
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "area": len(cells),
                    "bbox": (r1, r2, c1, c2),
                    "bbox_area": (r2 - r1 + 1) * (c2 - c1 + 1),
                    "crop": crop,
                }
            )
    return result


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    profile = _PROFILE_BY_SHAPE.get((height, width))
    if profile is None:
        errors.append(f"shape {(height, width)} is outside public profiles")

    palette = sorted({value for row in grid for value in row})
    if 0 not in palette:
        errors.append("background color 0 must be present")

    components = _objects(grid)
    if len(components) != 3:
        errors.append(f"found {len(components)} monochrome objects; expected exactly 3")

    object_colors = [obj["color"] for obj in components]
    if len(set(object_colors)) != len(object_colors):
        errors.append("the three objects must use distinct colors")

    sizes = tuple(sorted((obj["area"] for obj in components), reverse=True))
    area_pattern = _AREA_PATTERN_BY_SIZES.get(sizes)
    if area_pattern is None:
        errors.append(f"object areas {sizes} are outside public area patterns")

    cell_owner: dict[tuple[int, int], int] = {}
    for index, obj in enumerate(components):
        for cell in obj["cells"]:
            cell_owner[cell] = index
    for (row, col), owner in cell_owner.items():
        for dr, dc in _CARDINAL:
            neighbor = (row + dr, col + dc)
            if neighbor in cell_owner and cell_owner[neighbor] != owner:
                errors.append("different objects may not touch cardinally")
                break

    for index, first in enumerate(components):
        ar1, ar2, ac1, ac2 = first["bbox"]
        for second in components[index + 1 :]:
            br1, br2, bc1, bc2 = second["bbox"]
            overlap = not (ar2 < br1 or br2 < ar1 or ac2 < bc1 or bc2 < ac1)
            if overlap:
                errors.append("object bounding boxes must not overlap")

    return {
        "errors": list(dict.fromkeys(errors)),
        "profile": profile,
        "area_pattern": area_pattern,
        "components": components,
        "palette": palette,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the exact linked teaching grammar; never raise on bad grids."""
    del difficulty, meta
    return _analysis(grid)["errors"]


def strict_canonical_like(grid) -> list[str]:
    """Recognize the complete shape/area grammar represented publicly."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, str]:
    """Recover both exact public axes solely from returned pixels."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError(f"cannot observe malformed grid: {analysis['errors'][0]}")
    return {
        "profile": analysis["profile"],
        "area_pattern": analysis["area_pattern"],
    }


def _authority_key(obj: dict[str, Any]) -> tuple[int, int, int, int, int]:
    r1, r2, c1, c2 = obj["bbox"]
    return (-obj["area"], r1, r2, c1, c2)


def _gallery(crops: Sequence[Sequence[Sequence[int]]], *, bottom=False):
    if not crops:
        return [[0]]
    height = max(len(crop) for crop in crops)
    width = sum(len(crop[0]) for crop in crops) + len(crops) - 1
    output = full_grid(height, width, 0)
    left = 0
    for crop in crops:
        top = height - len(crop) if bottom else 0
        for row, values in enumerate(crop):
            for col, value in enumerate(values):
                output[top + row][left + col] = value
        left += len(crop[0]) + 1
    return output


def _ordered_output(grid, key: Callable[[dict[str, Any]], Any], *, bottom=False):
    errors = _rectangular_errors(grid)
    if errors:
        raise ValueError(errors[0])
    ordered = sorted(_objects(grid), key=key)
    return _gallery([obj["crop"] for obj in ordered], bottom=bottom)


def rule_mirror(grid):
    """Pure Python mirror of the selected Racket authority."""
    return _ordered_output(grid, _authority_key)


def _rival_ascending_area(grid):
    return _ordered_output(grid, lambda obj: (obj["area"], *obj["bbox"]))


def _rival_bbox_area(grid):
    return _ordered_output(grid, lambda obj: (-obj["bbox_area"], *obj["bbox"]))


def _rival_scan_order(grid):
    """Wrong shortcut: preserve ordinary row-major top-left discovery order."""
    def key(obj):
        r1, r2, c1, c2 = obj["bbox"]
        return (r1, c1, r2, c2)
    return _ordered_output(grid, key)


def _rival_color_order(grid):
    return _ordered_output(grid, lambda obj: (obj["color"], *obj["bbox"]))


def _rival_descending_color_order(grid):
    return _ordered_output(grid, lambda obj: (-obj["color"], *obj["bbox"]))


def _rival_tie_by_color(grid):
    return _ordered_output(
        grid, lambda obj: (-obj["area"], obj["color"], *obj["bbox"])
    )


def _rival_bottom_aligned(grid):
    return _ordered_output(grid, _authority_key, bottom=True)


SEMANTIC_RIVALS = {
    "ascending_area": _rival_ascending_area,
    "bbox_area": _rival_bbox_area,
    "scan_order": _rival_scan_order,
    "color_order": _rival_color_order,
    "descending_color_order": _rival_descending_color_order,
    "tie_by_color": _rival_tie_by_color,
    "bottom_aligned": _rival_bottom_aligned,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"tie_by_color": _rival_tie_by_color}


def _rival_differs(grid, rival: str) -> bool:
    return not self_check(grid) and SEMANTIC_RIVALS[rival](grid) != rule_mirror(grid)


def _witness_descending(grid) -> bool:
    return _rival_differs(grid, "ascending_area")


def _witness_cell_not_bbox_area(grid) -> bool:
    return _rival_differs(grid, "bbox_area")


def _witness_not_scan_order(grid) -> bool:
    return _rival_differs(grid, "scan_order")


def _witness_not_color_order(grid) -> bool:
    return _rival_differs(grid, "color_order")


def _witness_not_descending_color_order(grid) -> bool:
    return _rival_differs(grid, "descending_color_order")


def _witness_bbox_tie(grid) -> bool:
    return _rival_differs(grid, "tie_by_color")


def _witness_top_alignment(grid) -> bool:
    return _rival_differs(grid, "bottom_aligned")


SEMANTIC_WITNESSES = {
    "descending_not_ascending_area": _witness_descending,
    "cell_area_not_bbox_area": _witness_cell_not_bbox_area,
    "area_sort_not_scan_order": _witness_not_scan_order,
    "area_sort_not_color_order": _witness_not_color_order,
    "area_sort_not_descending_color_order": _witness_not_descending_color_order,
    "bbox_tie_not_color_tie": _witness_bbox_tie,
    "gallery_is_top_aligned": _witness_top_alignment,
}
WITNESS_RIVALS = {
    "descending_not_ascending_area": ["ascending_area"],
    "cell_area_not_bbox_area": ["bbox_area"],
    "area_sort_not_scan_order": ["scan_order"],
    "area_sort_not_color_order": ["color_order"],
    "area_sort_not_descending_color_order": ["descending_color_order"],
    "bbox_tie_not_color_tie": ["tie_by_color"],
    "gallery_is_top_aligned": ["bottom_aligned"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require valid labels and elimination of every declared competitor."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstration pairs"]
    reasons: list[str] = []
    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} is outside linked grammar: {errors[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with selected rule")
            continue
        valid_demos.append(pair)

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            if valid_demos and all(
                competitor(pair["input"]) == pair["output"] for pair in valid_demos
            ):
                reasons.append(f"competitor {name!r} survives every demonstration")
        except Exception as exc:  # pragma: no cover - diagnostic boundary
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is not an input/output pair")
    else:
        errors = self_check(query["input"])
        if errors:
            reasons.append(f"query is outside linked grammar: {errors[0]}")
        elif rule_mirror(query["input"]) != query["output"]:
            reasons.append("query output disagrees with selected rule")
    return reasons


def mutation_fixtures():
    """Small near-miss scenes that the structural validator must reject."""
    blank = full_grid(8, 13, 0)

    wrong_count = full_grid(8, 13, 0)
    _paint(wrong_count, _VERTICAL_3, 1, 1, 2)
    _paint(wrong_count, _SQUARE_4, 1, 4, 4)

    repeated_color = full_grid(8, 13, 0)
    _paint(repeated_color, _VERTICAL_3, 1, 1, 2)
    _paint(repeated_color, _SQUARE_4, 1, 4, 5)
    _paint(repeated_color, _T_4, 1, 8, 5)

    wrong_sizes = full_grid(8, 13, 0)
    _paint(wrong_sizes, _VERTICAL_3, 1, 1, 2)
    _paint(wrong_sizes, _SQUARE_4, 1, 4, 4)
    _paint(wrong_sizes, _PLUS_5, 1, 8, 7)

    touching = full_grid(8, 13, 0)
    _paint(touching, _VERTICAL_3, 1, 1, 2)
    _paint(touching, _SQUARE_4, 1, 2, 4)
    _paint(touching, _T_4, 1, 8, 7)

    return [
        ("blank", blank),
        ("two_objects", wrong_count),
        ("repeated_object_color", repeated_color),
        ("unsupported_area_pattern", wrong_sizes),
        ("touching_objects", touching),
    ]
