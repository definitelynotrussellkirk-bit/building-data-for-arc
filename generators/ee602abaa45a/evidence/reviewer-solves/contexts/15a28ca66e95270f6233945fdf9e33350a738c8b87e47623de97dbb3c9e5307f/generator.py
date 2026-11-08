"""Canonical-domain sampler for task ee602abaa45a.

Each of two rectangular frames contains two candidate templates, color 1 in the
left 3x3 slot and color 2 in the right 3x3 slot.  The frame's bottom interior
row stores a selector (1 or 2) and a transform code (3 identity, 4 rotate CW,
5 rotate 180, 6 flip left/right).  The selected template is tightly cropped,
transformed, recolored to the frame border, and the two results are packed in
frame reading order with one blank column and vertical centering.

The imported v2 sampler had already removed the unselected candidate, which
made the answer-bearing selector unnecessary.  This version restores the full
canonical grammar and schedules explicit counterexamples to plausible shortcut
rules while leaving the selected Racket authority unchanged.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "ee602abaa45a"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "9c5ac46b22bb"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A canonical 14/15 by 22-24 canvas holds two distinct color-7/8/9 "
    "rectangular frames. Each frame contains both candidate templates (colors "
    "1 and 2), a selector cell choosing one candidate, and transform code "
    "3/4/5/6 for identity/rotate-CW/rotate-180/flip-LR. Transform the selected "
    "tight crop, recolor it to the frame border, and h-stack the two pieces in "
    "frame reading order, vertically centered with a one-cell gap."
)

INVARIANTS = [
    "background is 0; the canvas is 14x22-24 or 15x22-24",
    "exactly two distinct rectangular frame components use distinct colors from 7,8,9",
    "every frame is width 9 and height 7 or 8 with both color-1 and color-2 candidates",
    "candidate 1 occupies the left 3x3 slot and candidate 2 the right 3x3 slot",
    "the bottom interior code row is selector 1/2, transform 3/4/5/6, then zeros",
    "the two selectors are complementary and the two transform codes are distinct",
]

_TRANSFORM_PAIRS = tuple(
    f"{first}-{second}"
    for first in range(3, 7)
    for second in range(3, 7)
    if first != second
)
_LAYOUT_ORDERS = ("left_first", "right_first")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "sample-index schedule over canonical heights",
        "valid": "14..15",
    },
    "grid_w": {
        "type": "int",
        "default": "sample-index schedule over canonical widths",
        "valid": "22..24",
    },
    "selector_first": {
        "type": "int",
        "default": "alternates 1,2,1,2 in frame reading order",
        "valid": "1..2",
    },
    "transform_pair": {
        "type": "enum",
        "default": "four-profile schedule with distinct local transform codes",
        "valid": [
            "3-4", "3-5", "3-6", "4-3", "4-5", "4-6",
            "5-3", "5-4", "5-6", "6-3", "6-4", "6-5",
        ],
    },
    "layout_order": {
        "type": "enum",
        "default": "alternates left-first and right-first reading order",
        "valid": ["left_first", "right_first"],
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

# Defaults deliberately cover canonical profiles and shortcut counterexamples.
# selected_shapes are named in frame reading order, not physical left/right order.
_PROFILE_DEFAULTS = (
    {
        "name": "line_then_j_right",
        "grid_h": 14,
        "grid_w": 22,
        "selector_first": 1,
        "transform_pair": "4-6",
        "layout_order": "left_first",
        "selected_shapes": ("line_v", "j4"),
    },
    {
        "name": "ell_then_j_crossed",
        "grid_h": 15,
        "grid_w": 23,
        "selector_first": 2,
        "transform_pair": "5-4",
        "layout_order": "right_first",
        "selected_shapes": ("ell3", "j4"),
    },
    {
        "name": "j_then_ell_wide",
        "grid_h": 14,
        "grid_w": 24,
        "selector_first": 1,
        "transform_pair": "3-6",
        "layout_order": "left_first",
        "selected_shapes": ("j4", "ell3"),
    },
    {
        "name": "j_then_line_crossed",
        "grid_h": 15,
        "grid_w": 22,
        "selector_first": 2,
        "transform_pair": "6-3",
        "layout_order": "right_first",
        "selected_shapes": ("j4", "line_h"),
    },
)
SCHEDULE_PROFILES = tuple(profile["name"] for profile in _PROFILE_DEFAULTS)
_DIFFICULTY_OFFSETS = {None: 0, "easy": 0, "medium": 1, "hard": 2}

_SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "line_h": ((0, 0), (0, 1), (0, 2)),
    "line_v": ((0, 0), (1, 0), (2, 0)),
    "ell3": ((0, 0), (1, 0), (1, 1)),
    "j4": ((0, 0), (1, 0), (2, 0), (2, 1)),
}


def _profile_index(sample_index: int, difficulty: str | None) -> int:
    if difficulty not in _DIFFICULTY_OFFSETS:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return (int(sample_index) + _DIFFICULTY_OFFSETS[difficulty]) % len(_PROFILE_DEFAULTS)


def schedule_profile(seed, sample_index, difficulty=None):
    del seed
    return _PROFILE_DEFAULTS[_profile_index(sample_index, difficulty)]["name"]


def _scheduled_int(ctx, label: str, lo: int, hi: int, default: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _scheduled_choice(ctx, label: str, options: tuple[str, ...], default: str) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _rotate_cells_cw(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalize((c, -r) for r, c in cells)


def _flip_cells_lr(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalize((r, -c) for r, c in cells)


def _shape_variants(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    variants: list[tuple[tuple[int, int], ...]] = []
    seen: set[tuple[tuple[int, int], ...]] = set()
    for reflected in (False, True):
        current = _flip_cells_lr(cells) if reflected else _normalize(cells)
        for _ in range(4):
            if current not in seen:
                seen.add(current)
                variants.append(current)
            current = _rotate_cells_cw(current)
    return tuple(variants)


def _strict_int_override(name: str, value, lo: int, hi: int) -> None:
    if value is None:
        return
    if isinstance(value, bool) or type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an integer in {lo}..{hi}")


def _validate_overrides(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    _strict_int_override("grid_h", overrides.get("grid_h"), 14, 15)
    _strict_int_override("grid_w", overrides.get("grid_w"), 22, 24)
    _strict_int_override("selector_first", overrides.get("selector_first"), 1, 2)
    if overrides.get("transform_pair") is not None:
        value = overrides["transform_pair"]
        if type(value) is not str or value not in _TRANSFORM_PAIRS:
            raise ValueError(f"transform_pair must be one of {_TRANSFORM_PAIRS}")
    if overrides.get("layout_order") is not None:
        value = overrides["layout_order"]
        if type(value) is not str or value not in _LAYOUT_ORDERS:
            raise ValueError(f"layout_order must be one of {_LAYOUT_ORDERS}")


def _choose_variant(ctx, label: str, shape_name: str, *, fixed: bool) -> tuple[tuple[int, int], ...]:
    variants = _shape_variants(_SHAPES[shape_name])
    if fixed:
        return variants[0]
    return ctx.draw_rng(label).choice(variants)


def _place_shape(
    grid: list[list[int]],
    *,
    frame_top: int,
    frame_left: int,
    slot_left: int,
    color: int,
    cells: tuple[tuple[int, int], ...],
    rng,
) -> None:
    height = max(r for r, _ in cells) + 1
    width = max(c for _, c in cells) + 1
    row_offset = rng.randint(0, 3 - height)
    col_offset = rng.randint(0, 3 - width)
    for row, col in cells:
        grid[frame_top + 1 + row_offset + row][
            frame_left + 1 + slot_left + col_offset + col
        ] = color


def _horizontal_positions(width: int, rng) -> tuple[int, int]:
    candidates = [
        (left, right)
        for left in (1, 2)
        for right in (width - 11, width - 10)
        if right >= 1 and right + 8 < width and right - (left + 8) >= 2
    ]
    if not candidates:
        raise ValueError(f"width {width} cannot fit two canonical frames")
    return rng.choice(candidates)


def _vertical_positions(
    height: int,
    first_height: int,
    second_height: int,
    layout_order: str,
    rng,
) -> tuple[int, int]:
    max_first = height - first_height - 1
    max_second = height - second_height - 1
    if layout_order == "left_first":
        first_top = rng.randint(1, min(3, max_first))
        second_top = rng.randint(first_top, min(max_second, first_top + 3))
    else:
        first_top = rng.randint(1, min(2, max_first))
        low = first_top + 1
        high = min(max_second, first_top + 3)
        if low > high:
            raise ValueError("canvas cannot realize right-first reading order")
        second_top = rng.randint(low, high)
    return first_top, second_top


def _draw_one_frame(
    grid: list[list[int]],
    *,
    top: int,
    left: int,
    frame_height: int,
    frame_color: int,
    selector: int,
    transform: int,
    selected_shape: str,
    ctx,
    frame_index: int,
    fixed_selected_orientation: bool,
) -> None:
    bottom = top + frame_height - 1
    right = left + 8
    draw_frame(grid, top, left, bottom, right, frame_color)

    distractor_shape = "j4" if selected_shape != "j4" else "ell3"
    candidate_names = {
        selector: selected_shape,
        3 - selector: distractor_shape,
    }
    for candidate_color, slot_left in ((1, 0), (2, 3)):
        is_selected = candidate_color == selector
        cells = _choose_variant(
            ctx,
            f"shape_variant_{frame_index}_{candidate_color}",
            candidate_names[candidate_color],
            fixed=is_selected and fixed_selected_orientation,
        )
        _place_shape(
            grid,
            frame_top=top,
            frame_left=left,
            slot_left=slot_left,
            color=candidate_color,
            cells=cells,
            rng=ctx.draw_rng(f"shape_offset_{frame_index}_{candidate_color}"),
        )

    code_row = bottom - 1
    grid[code_row][left + 1] = selector
    grid[code_row][left + 2] = transform


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    profile_index = _profile_index(sample_index, difficulty)
    profile = _PROFILE_DEFAULTS[profile_index]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    height = _scheduled_int(ctx, "grid_h", 14, 15, profile["grid_h"])
    width = _scheduled_int(ctx, "grid_w", 22, 24, profile["grid_w"])
    selector_first = _scheduled_int(
        ctx, "selector_first", 1, 2, profile["selector_first"]
    )
    transform_pair = _scheduled_choice(
        ctx, "transform_pair", _TRANSFORM_PAIRS, profile["transform_pair"]
    )
    layout_order = _scheduled_choice(
        ctx, "layout_order", _LAYOUT_ORDERS, profile["layout_order"]
    )
    transforms = tuple(int(value) for value in transform_pair.split("-"))
    selectors = (selector_first, 3 - selector_first)

    frame_colors = tuple(ctx.draw_rng("frame_colors").sample((7, 8, 9), 2))
    height_rng = ctx.draw_rng("frame_heights")
    frame_heights = (height_rng.choice((7, 8)), height_rng.choice((7, 8)))
    left_col, right_col = _horizontal_positions(width, ctx.draw_rng("horizontal_positions"))
    first_top, second_top = _vertical_positions(
        height,
        frame_heights[0],
        frame_heights[1],
        layout_order,
        ctx.draw_rng("vertical_positions"),
    )

    if layout_order == "left_first":
        positions = ((first_top, left_col), (second_top, right_col))
    else:
        positions = ((first_top, right_col), (second_top, left_col))

    grid = full_grid(height, width, 0)
    for index in range(2):
        _draw_one_frame(
            grid,
            top=positions[index][0],
            left=positions[index][1],
            frame_height=frame_heights[index],
            frame_color=frame_colors[index],
            selector=selectors[index],
            transform=transforms[index],
            selected_shape=profile["selected_shapes"][index],
            ctx=ctx,
            frame_index=index,
            fixed_selected_orientation=profile_index in (0, 3),
        )

    issues = self_check(grid, difficulty=difficulty)
    if issues:
        raise AssertionError(f"internal generator drift: {issues}")
    return grid


def _high_components(grid: list[list[int]]) -> list[dict]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict] = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color < 7 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [row for row, _ in cells]
            cols = [col for _, col in cells]
            components.append(
                {
                    "color": color,
                    "cells": set(cells),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return components


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            point = (row + dr, col + dc)
            if point in cells and point not in seen:
                seen.add(point)
                stack.append(point)
    return seen == cells


def _analyze(grid) -> dict:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return {"errors": ["grid must be a nonempty list of rows"], "frames": []}
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        return {"errors": ["grid must be nonempty and rectangular"], "frames": []}
    for row in grid:
        for value in row:
            if isinstance(value, bool) or type(value) is not int or not 0 <= value <= 9:
                return {"errors": ["grid values must be integer colors 0..9"], "frames": []}

    height = len(grid)
    if height not in (14, 15):
        errors.append(f"height must be 14 or 15, found {height}")
    if width not in (22, 23, 24):
        errors.append(f"width must be 22..24, found {width}")

    components = _high_components(grid)
    if len(components) != 2:
        errors.append(f"expected exactly two frame components, found {len(components)}")

    parsed: list[dict] = []
    occupied_rectangles: set[tuple[int, int]] = set()
    for index, component in enumerate(components):
        r0, c0, r1, c1 = component["bbox"]
        frame_height = r1 - r0 + 1
        frame_width = c1 - c0 + 1
        border = {
            (row, col)
            for row in range(r0, r1 + 1)
            for col in range(c0, c1 + 1)
            if row in (r0, r1) or col in (c0, c1)
        }
        if frame_height not in (7, 8) or frame_width != 9:
            errors.append(
                f"frame {index} must be height 7/8 and width 9, found {frame_height}x{frame_width}"
            )
        if component["cells"] != border:
            errors.append(f"frame {index} border is incomplete or has high-color interior cells")
        rectangle = {
            (row, col)
            for row in range(r0, r1 + 1)
            for col in range(c0, c1 + 1)
        }
        if occupied_rectangles & rectangle:
            errors.append("frame rectangles overlap")
        occupied_rectangles.update(rectangle)

        if frame_height < 3 or frame_width < 3:
            continue
        code_row = r1 - 1
        code_values = [grid[code_row][col] for col in range(c0 + 1, c1)]
        selector = code_values[0] if code_values else None
        transform = code_values[1] if len(code_values) > 1 else None
        if selector not in (1, 2):
            errors.append(f"frame {index} selector must be 1 or 2, found {selector}")
        if transform not in (3, 4, 5, 6):
            errors.append(f"frame {index} transform must be 3..6, found {transform}")
        if code_values[2:] != [0] * max(0, len(code_values) - 2):
            errors.append(f"frame {index} code row has extra nonzero cells")

        candidates: dict[int, set[tuple[int, int]]] = {}
        for candidate_color, col_lo, col_hi in ((1, 0, 2), (2, 3, 5)):
            cells = {
                (row, col)
                for row in range(r0 + 1, min(r0 + 4, code_row))
                for col in range(c0 + 1 + col_lo, c0 + 2 + col_hi)
                if grid[row][col] == candidate_color
            }
            candidates[candidate_color] = cells
            if len(cells) not in (3, 4):
                errors.append(
                    f"frame {index} candidate {candidate_color} must have 3 or 4 cells, found {len(cells)}"
                )
            elif not _connected(cells):
                errors.append(f"frame {index} candidate {candidate_color} is disconnected")

        for row in range(r0 + 1, code_row):
            for col in range(c0 + 1, c1):
                value = grid[row][col]
                in_candidate_slot = (
                    row <= r0 + 3
                    and (
                        (c0 + 1 <= col <= c0 + 3 and value in (0, 1))
                        or (c0 + 4 <= col <= c0 + 6 and value in (0, 2))
                        or (col == c0 + 7 and value == 0)
                    )
                )
                if not in_candidate_slot and value != 0:
                    errors.append(f"frame {index} has a nonzero cell outside candidate slots")
                    break

        parsed.append(
            {
                "color": component["color"],
                "bbox": component["bbox"],
                "selector": selector,
                "transform": transform,
                "candidates": candidates,
            }
        )

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0 and (row, col) not in occupied_rectangles:
                errors.append("nonzero cells must lie inside one of the two frames")
                break

    parsed.sort(key=lambda frame: frame["bbox"][:2])
    if len(parsed) == 2:
        if parsed[0]["color"] == parsed[1]["color"]:
            errors.append("frame colors must be distinct")
        if {parsed[0]["selector"], parsed[1]["selector"]} != {1, 2}:
            errors.append("the two selectors must be complementary 1 and 2")
        if parsed[0]["transform"] == parsed[1]["transform"]:
            errors.append("the two transform codes must be distinct")
        palette = {value for row in grid for value in row}
        if len(palette) != 7:
            errors.append(f"canonical palette must contain exactly 7 colors, found {len(palette)}")
    return {"errors": errors, "frames": parsed}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return _analyze(grid)["errors"]


def strict_canonical_like(grid) -> list[str]:
    return _analyze(grid)["errors"]


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError(analysis["errors"][0])
    first, second = analysis["frames"]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "selector_first": first["selector"],
        "transform_pair": f"{first['transform']}-{second['transform']}",
        "layout_order": (
            "left_first"
            if first["bbox"][1] < second["bbox"][1]
            else "right_first"
        ),
    }


def _crop_cells(cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    cells = list(cells)
    if not cells:
        return [[0]]
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    bottom = max(row for row, _ in cells)
    right = max(col for _, col in cells)
    result = [[0] * (right - left + 1) for _ in range(bottom - top + 1)]
    for row, col in cells:
        result[row - top][col - left] = 1
    return result


def _rotate_grid_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _transform_grid(grid: list[list[int]], code: int) -> list[list[int]]:
    if code == 3:
        return deepcopy(grid)
    if code == 4:
        return _rotate_grid_cw(grid)
    if code == 5:
        return [row[::-1] for row in grid[::-1]]
    if code == 6:
        return [row[::-1] for row in grid]
    raise ValueError(f"unsupported transform code {code}")


def rule_mirror(
    grid,
    *,
    selector_override: int | None = None,
    ignore_transform: bool = False,
    left_to_right: bool = False,
    top_align: bool = False,
) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError(analysis["errors"][0])
    frames = list(analysis["frames"])
    if left_to_right:
        frames.sort(key=lambda frame: (frame["bbox"][1], frame["bbox"][0]))

    pieces: list[list[list[int]]] = []
    for frame in frames:
        selector = selector_override or frame["selector"]
        pattern = _crop_cells(frame["candidates"][selector])
        transformed = _transform_grid(pattern, 3 if ignore_transform else frame["transform"])
        pieces.append(
            [
                [frame["color"] if value else 0 for value in row]
                for row in transformed
            ]
        )

    height = max(len(piece) for piece in pieces)
    width = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    result = [[0] * width for _ in range(height)]
    left = 0
    for piece in pieces:
        top = 0 if top_align else (height - len(piece)) // 2
        for row, values in enumerate(piece):
            for col, value in enumerate(values):
                if value:
                    result[top + row][left + col] = value
        left += len(piece[0]) + 1
    return result


def _rival_always_candidate_1(grid):
    return rule_mirror(grid, selector_override=1)


def _rival_always_candidate_2(grid):
    return rule_mirror(grid, selector_override=2)


def _rival_ignore_transform(grid):
    return rule_mirror(grid, ignore_transform=True)


def _rival_left_to_right(grid):
    return rule_mirror(grid, left_to_right=True)


def _rival_top_align(grid):
    return rule_mirror(grid, top_align=True)


SEMANTIC_RIVALS: dict[str, Callable] = {
    "always_candidate_1": _rival_always_candidate_1,
    "always_candidate_2": _rival_always_candidate_2,
    "ignore_transform": _rival_ignore_transform,
    "left_to_right": _rival_left_to_right,
    "top_align": _rival_top_align,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"top_align": _rival_top_align}


def _witness_candidate_1(grid) -> bool:
    return _rival_always_candidate_1(grid) != rule_mirror(grid)


def _witness_candidate_2(grid) -> bool:
    return _rival_always_candidate_2(grid) != rule_mirror(grid)


def _witness_transform(grid) -> bool:
    return _rival_ignore_transform(grid) != rule_mirror(grid)


def _witness_reading_order(grid) -> bool:
    return _rival_left_to_right(grid) != rule_mirror(grid)


def _witness_vertical_centering(grid) -> bool:
    return _rival_top_align(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES: dict[str, Callable] = {
    "selector_one_changes_answer": _witness_candidate_1,
    "selector_two_changes_answer": _witness_candidate_2,
    "transform_changes_answer": _witness_transform,
    "reading_order_crosses_columns": _witness_reading_order,
    "vertical_centering_changes_answer": _witness_vertical_centering,
}
WITNESS_RIVALS = {
    "selector_one_changes_answer": ["always_candidate_1"],
    "selector_two_changes_answer": ["always_candidate_2"],
    "transform_changes_answer": ["ignore_transform"],
    "reading_order_crosses_columns": ["left_to_right"],
    "vertical_centering_changes_answer": ["top_align"],
}


def lesson_identifiable(demos, query) -> list[str]:
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    reasons: list[str] = []
    valid_demos: list[dict] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        try:
            expected = rule_mirror(demo["input"])
        except ValueError as exc:
            reasons.append(f"demo {index} is outside the task grammar: {exc}")
            continue
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the pinned rule")
            continue
        valid_demos.append(demo)
    try:
        query_answer = rule_mirror(query["input"])
    except ValueError as exc:
        reasons.append(f"query is outside the task grammar: {exc}")
        return reasons
    if query.get("output") is not None and query["output"] != query_answer:
        reasons.append("query output disagrees with the pinned rule")
    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo["output"] for demo in valid_demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons
