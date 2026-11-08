"""Constructive generator for 5b4fd0a9c80e — stack component crops by area.

The unchanged Racket authority extracts same-color 4-connected components,
sorts them by ``(cell_count, bbox_top, bbox_left)``, crops each bounding box,
and vertically stacks the crops with one blank row while centering every crop
against the widest crop.

The four-profile schedule alternates distinct-area sorts with positional ties.
Every three-demo cyclic window refutes source order, move-largest-last, bbox-area
sorting, color ordering, left/right-biased packing, and omitted separator rows.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5b4fd0a9c80e"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "d54b19002e00"

SUMMARY = (
    "Place three separated monochrome components. Sort their raw bbox crops by "
    "ascending cell area with top-row/left-column tie breaks, then stack them "
    "with one blank row and floor-centered horizontal alignment. The four-profile "
    "schedule mixes distinct sizes, positional ties, bbox-area traps, and odd "
    "centering offsets."
)

INVARIANTS = [
    "background is 0 and there are exactly three distinct-color 4-connected components",
    "profiles 0 and 2 have three distinct areas and defeat move-largest-last and bbox-area sorting",
    "profile 1 makes top-row priority conflict with left-column order for equal areas",
    "profile 3 gives equal-area components the same top row so left-column is the secondary key",
    "every profile has an odd crop-width difference exposing left and right-biased centering",
]

AXES = {
    "grid_h": {"type": "int", "default": "linked canonical profile", "valid": "10..14"},
    "grid_w": {"type": "int", "default": "linked canonical profile", "valid": "12..16"},
    "shape_profile": {"type": "int", "default": "sample_index mod 4", "valid": "0..3"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (
    "distinct_3_5_7_bbox_conflict",
    "tie4_top_before_left",
    "distinct_4_6_7_largest_last_trap",
    "tie5_left_secondary",
)

_PALETTE = tuple(range(1, 10))
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DEFAULT_DIMS = (
    (10, 12),
    (11, 13),
    (12, 12),
    (10, 14),
)
_DIFFICULTY_PROFILE_OFFSET = {None: 0, "easy": 0, "medium": 1, "hard": 2}

_L3 = ((0, 0), (1, 0), (1, 1))
_PLUS5 = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
_WIDE7 = ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2))
_V4 = tuple((row, 0) for row in range(4))
_H4 = tuple((0, col) for col in range(4))
_RECT6 = tuple((row, col) for row in range(2) for col in range(3))
_SPARSE6 = ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1))
_V5 = tuple((row, 0) for row in range(5))
_WIDE5 = ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0))
_U7 = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2))

# Component order here is source/scan order, deliberately not the answer order.
_PROFILE_SHAPES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    0: (_PLUS5, _WIDE7, _L3),
    1: (_V4, _RECT6, _H4),
    2: (_SPARSE6, _V4, _WIDE7),
    3: (_U7, _V5, _WIDE5),
}
_PROFILE_SIGNATURES = {
    tuple(sorted(len(shape) for shape in shapes)): profile
    for profile, shapes in _PROFILE_SHAPES.items()
}


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Expose the finite, band-shifted teaching schedule to review tooling."""
    del seed
    if difficulty not in _DIFFICULTY_PROFILE_OFFSET:
        raise ValueError(f"unknown difficulty {difficulty!r}")
    profile = (sample_index + _DIFFICULTY_PROFILE_OFFSET[difficulty]) % len(SCHEDULE_PROFILES)
    return SCHEDULE_PROFILES[profile]


def _validate_request(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    bounds = {"grid_h": (10, 14), "grid_w": (12, 16), "shape_profile": (0, 3)}
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"override {name!r} must be an integer, got {value!r}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"override {name!r}={value} outside [{lo}, {hi}]")


def _draw_axis(ctx, overrides: dict[str, Any], name: str, domain: tuple[int, ...], default: int) -> int:
    options = domain if overrides.get(name) is not None else (default,)
    return ctx.draw_choice(name, options)


def _bbox(cells: tuple[tuple[int, int], ...]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_dims(cells: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    top, left, bottom, right = _bbox(cells)
    return bottom - top + 1, right - left + 1


def _normalize(shape: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    top = min(row for row, _ in shape)
    left = min(col for _, col in shape)
    return tuple(sorted((row - top, col - left) for row, col in shape))


def _reflect(shape: tuple[tuple[int, int], ...], *, vertical: bool, horizontal: bool):
    height, width = _bbox_dims(shape)
    transformed = []
    for row, col in shape:
        transformed.append((height - 1 - row if vertical else row, width - 1 - col if horizontal else col))
    return _normalize(tuple(transformed))


def _place(grid: list[list[int]], shape: tuple[tuple[int, int], ...], top: int, left: int, color: int) -> None:
    for row, col in shape:
        if grid[top + row][left + col] != 0:
            raise RuntimeError("constructive placement collision")
        grid[top + row][left + col] = color


def _random_col(rng, width: int, shape: tuple[tuple[int, int], ...]) -> int:
    return rng.randint(0, width - _bbox_dims(shape)[1])


def _profile_placements(
    profile: int,
    shapes: tuple[tuple[tuple[int, int], ...], ...],
    height: int,
    width: int,
    rng,
) -> tuple[tuple[int, int], ...]:
    """Construct source-order layouts carrying each profile's teaching contrast."""
    if profile == 0:
        required = sum(_bbox_dims(shape)[0] for shape in shapes) + 2
        top = rng.randint(0, height - required)
        rows = (top, top + _bbox_dims(shapes[0])[0] + 1, top + _bbox_dims(shapes[0])[0] + _bbox_dims(shapes[1])[0] + 2)
        return tuple((row, _random_col(rng, width, shape)) for row, shape in zip(rows, shapes))

    if profile == 1:
        # Equal area-4 crops conflict on the two positional keys: the first is
        # higher but farther right, so top row must dominate left column.
        top = rng.randint(0, height - 9)
        rows = (top, top + 5, top + 8)
        upper_right = rng.randint(max(width // 2 + 1, 6), width - 1)
        lower_left = rng.randint(0, min(width // 3, upper_right - 1))
        return (
            (rows[0], upper_right),
            (rows[1], _random_col(rng, width, shapes[1])),
            (rows[2], lower_left),
        )

    if profile == 2:
        # Source order is area 6, 4, 7.  Merely moving the largest crop last
        # leaves 6 before 4, while bbox-area sorting swaps the final two.
        top = rng.randint(0, height - 10)
        rows = (top, top + 4, top + 8)
        return tuple((row, _random_col(rng, width, shape)) for row, shape in zip(rows, shapes))

    if profile == 3:
        # The tied area-5 crops share a top row, making left column observable
        # as the secondary key.  The larger crop appears first in source order.
        top = rng.randint(0, height - 9)
        tie_top = top + 4
        gap = rng.randint(2, min(4, width - 5))
        span = 1 + gap + 4
        left = rng.randint(0, width - span)
        return (
            (top, _random_col(rng, width, shapes[0])),
            (tie_top, left),
            (tie_top, left + 1 + gap),
        )

    raise ValueError(f"unknown shape profile {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scheduled_profile = (
        sample_index + _DIFFICULTY_PROFILE_OFFSET[difficulty]
    ) % len(SCHEDULE_PROFILES)
    profile = _draw_axis(ctx, overrides, "shape_profile", tuple(range(4)), scheduled_profile)
    default_h, default_w = _DEFAULT_DIMS[profile]
    height = _draw_axis(ctx, overrides, "grid_h", tuple(range(10, 15)), default_h)
    width = _draw_axis(ctx, overrides, "grid_w", tuple(range(12, 17)), default_w)

    shapes = tuple(
        _reflect(
            shape,
            vertical=bool(ctx.draw_rng(f"shape_transform_{index}").randrange(2)),
            horizontal=bool(ctx.draw_rng(f"shape_transform_{index}").randrange(2)),
        )
        for index, shape in enumerate(_PROFILE_SHAPES[profile])
    )
    placements = _profile_placements(
        profile, shapes, height, width, ctx.draw_rng("constructive_layout")
    )

    low, middle, high = sorted(ctx.draw_rng("palette").sample(_PALETTE, 3))
    colors_by_profile = {
        0: (high, low, middle),
        1: (high, middle, low),
        2: (high, middle, low),
        3: (middle, high, low),
    }
    colors = colors_by_profile[profile]

    grid = full_grid(height, width, 0)
    for shape, (row, col), color in zip(shapes, placements, colors):
        _place(grid, shape, row, col, color)

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructed invalid grid: {errors}")
    return grid


def _coerce_rectangular_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return None, ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["grid is ragged"]
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                return None, [f"cell ({row_index},{col_index}) is not an integer color 0..9"]
    return grid, []


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            normalized = tuple(sorted(cells))
            result.append(
                {
                    "color": color,
                    "cells": normalized,
                    "size": len(normalized),
                    "bbox": _bbox(normalized),
                }
            )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full task-domain envelope without raising on malformed input."""
    del difficulty, meta
    checked, errors = _coerce_rectangular_grid(grid)
    if errors:
        return errors
    assert checked is not None
    height, width = len(checked), len(checked[0])
    if not 10 <= height <= 14:
        errors.append(f"grid height {height} outside 10..14")
    if not 12 <= width <= 16:
        errors.append(f"grid width {width} outside 12..16")

    components = _components(checked)
    if len(components) != 3:
        errors.append(f"expected exactly 3 components, found {len(components)}")
    colors = [component["color"] for component in components]
    if len(colors) != len(set(colors)):
        errors.append("component colors must be distinct")
    for index, component in enumerate(components):
        if not 3 <= component["size"] <= 7:
            errors.append(f"component {index} area {component['size']} outside 3..7")
        bbox_height, bbox_width = _bbox_dims(component["cells"])
        if bbox_height > 5 or bbox_width > 5:
            errors.append(f"component {index} bbox {bbox_height}x{bbox_width} exceeds 5x5")
    return errors


def _crop_component(grid: list[list[int]], component: dict[str, Any]) -> list[list[int]]:
    """Return the authority's raw bounding-box crop for one component."""
    top, left, bottom, right = component["bbox"]
    return [row[left : right + 1] for row in grid[top : bottom + 1]]


def _pack_components(
    grid: Any,
    *,
    order: str = "area",
    alignment: str = "center",
    gap: int = 1,
) -> list[list[int]]:
    """Small executable mirror used by semantic review tooling."""
    checked, errors = _coerce_rectangular_grid(grid)
    if errors or checked is None:
        raise ValueError(errors[0] if errors else "invalid grid")
    components = _components(checked)
    if not components:
        raise ValueError("grid contains no non-background components")

    if order == "area":
        components.sort(key=lambda item: (item["size"], item["bbox"][0], item["bbox"][1]))
    elif order == "source":
        components.sort(key=lambda item: (item["bbox"][0], item["bbox"][1]))
    elif order == "color_tie":
        components.sort(
            key=lambda item: (item["size"], item["color"], item["bbox"][0], item["bbox"][1])
        )
    elif order == "color_only":
        components.sort(key=lambda item: item["color"])
    elif order == "bbox_area":
        components.sort(
            key=lambda item: (
                (item["bbox"][2] - item["bbox"][0] + 1)
                * (item["bbox"][3] - item["bbox"][1] + 1),
                item["bbox"][0],
                item["bbox"][1],
            )
        )
    elif order == "move_largest_last":
        components.sort(key=lambda item: (item["bbox"][0], item["bbox"][1]))
        largest_index = max(range(len(components)), key=lambda index: components[index]["size"])
        largest = components.pop(largest_index)
        components.append(largest)
    else:
        raise ValueError(f"unknown component order {order!r}")
    if alignment not in {"center", "left", "right_bias"}:
        raise ValueError(f"unknown alignment {alignment!r}")
    if gap < 0:
        raise ValueError("gap must be nonnegative")

    crops = [_crop_component(checked, component) for component in components]
    output_width = max(len(crop[0]) for crop in crops)
    output_height = sum(len(crop) for crop in crops) + gap * (len(crops) - 1)
    output = full_grid(output_height, output_width, 0)
    output_top = 0
    for crop in crops:
        if alignment == "left":
            output_left = 0
        elif alignment == "right_bias":
            output_left = (output_width - len(crop[0]) + 1) // 2
        else:
            output_left = (output_width - len(crop[0])) // 2
        for row_index, row in enumerate(crop):
            output[output_top + row_index][output_left : output_left + len(row)] = row
        output_top += len(crop) + gap
    return output


def rule_mirror(grid: Any) -> list[list[int]]:
    """Executable Python mirror of the unchanged Racket authority."""
    return _pack_components(grid)


def _left_align_rival(grid: Any) -> list[list[int]]:
    return _pack_components(grid, alignment="left")


def _right_bias_center_rival(grid: Any) -> list[list[int]]:
    return _pack_components(grid, alignment="right_bias")


def _color_tie_break_rival(grid: Any) -> list[list[int]]:
    return _pack_components(grid, order="color_tie")


def _color_order_rival(grid: Any) -> list[list[int]]:
    return _pack_components(grid, order="color_only")


def _source_order_rival(grid: Any) -> list[list[int]]:
    return _pack_components(grid, order="source")


def _move_largest_last_rival(grid: Any) -> list[list[int]]:
    return _pack_components(grid, order="move_largest_last")


def _bbox_area_sort_rival(grid: Any) -> list[list[int]]:
    return _pack_components(grid, order="bbox_area")


def _omit_separator_rows_rival(grid: Any) -> list[list[int]]:
    return _pack_components(grid, gap=0)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "left_align": _left_align_rival,
    "right_bias_center": _right_bias_center_rival,
    "color_tie_break": _color_tie_break_rival,
    "color_order": _color_order_rival,
    "source_order": _source_order_rival,
    "move_largest_last": _move_largest_last_rival,
    "bbox_area_sort": _bbox_area_sort_rival,
    "omit_separator_rows": _omit_separator_rows_rival,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    name: (lambda grid, rival=rival: rival(grid) != rule_mirror(grid))
    for name, rival in SEMANTIC_RIVALS.items()
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}
# Left alignment fits every canonical label; generated profiles expose it.
CANONICAL_SHORTCUTS = {"left_align": _left_align_rival}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Check the finite declared-rival teaching contract for one lesson."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        findings = self_check(pair["input"])
        if findings:
            reasons.append(f"demo {index} malformed: {findings[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output does not match stack-by-area rule")
            continue
        valid_demos.append(pair)

    for name, competitor in LESSON_COMPETITORS.items():
        if valid_demos and all(
            competitor(pair["input"]) == pair["output"] for pair in valid_demos
        ):
            reasons.append(f"competitor {name!r} survives every demonstration")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input pair")
    else:
        findings = self_check(query["input"])
        if findings:
            reasons.append(f"query malformed: {findings[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match stack-by-area rule")
    return reasons


def _profile_from_components(components: list[dict[str, Any]]) -> int:
    signature = tuple(sorted(component["size"] for component in components))
    if signature not in _PROFILE_SIGNATURES:
        raise ValueError(f"area signature {signature!r} does not identify a shape profile")
    return _PROFILE_SIGNATURES[signature]


def observe_overrides(grid) -> dict[str, int]:
    checked, errors = _coerce_rectangular_grid(grid)
    if errors or checked is None:
        raise ValueError(errors[0] if errors else "invalid grid")
    structural = self_check(checked)
    if structural:
        raise ValueError(structural[0])
    return {
        "grid_h": len(checked),
        "grid_w": len(checked[0]),
        "shape_profile": _profile_from_components(_components(checked)),
    }


def strict_canonical_like(grid) -> list[str]:
    """The sampled grammar stays inside canonical scale, palette and object count."""
    return self_check(grid)
