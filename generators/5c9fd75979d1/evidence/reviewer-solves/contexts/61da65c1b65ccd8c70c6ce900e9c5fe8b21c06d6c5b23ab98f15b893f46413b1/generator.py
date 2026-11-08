"""Generator for ARC rule family 5c9fd75979d1 (source task 80214e03).

The input contains a dense, noisy grid of colored slot objects inside a zero
margin.  Object bounding-box edges define the row and column intervals; small
detached fragments are ignored.  The output is the slot-color matrix with its
columns reversed.

Defaults preserve all four complete published scene profiles.  Color names,
one-cell partition jitter, core placement, and individual holes vary while
the linked output shape and repeated-color pattern remain answer-bearing.
"""
from __future__ import annotations

from collections import deque
from itertools import product

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "5c9fd75979d1"
TASK_ID = "5c9fd75979d1"
VERSION = "3.0.0"
RULE_HASH = "36b024575e05"

SUMMARY = (
    "Find nonzero 4-connected objects whose bounding-box area exceeds two. "
    "Use all retained bounding-box top/bottom and left/right edges to define "
    "a slot grid, read the covering object's color in every slot, and reverse "
    "the slot-matrix columns."
)

INVARIANTS = [
    "the canvas and slot-matrix shape match one complete demonstrated profile",
    "all nonzero cells lie inside one zero-margined rectangular slot grid",
    "each slot contains only zero and its linked role color",
    "each slot's retained object spans its full bounding box despite holes",
    "the demonstrated repeated-color pattern and color cardinality are exact",
    "at least one interior hole distinguishes noisy objects from solid tiles",
]

SCENE_PROFILES = (
    "noisy_3x3_repeat6",
    "noisy_2x2_distinct4",
    "noisy_2x3_distinct6",
    "noisy_4x3_repeat8",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "uniform complete demonstrated noisy-slot profile",
        "valid": (
            "noisy_3x3_repeat6|noisy_2x2_distinct4|"
            "noisy_2x3_distinct6|noisy_4x3_repeat8"
        ),
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()


def _nearby_partitions(base):
    """Return one-cell local jitter that preserves total core size."""
    return tuple(sorted({
        tuple(base[index] + delta[index] for index in range(len(base)))
        for delta in product((-1, 0, 1), repeat=len(base))
        if all(base[index] + delta[index] >= 3 for index in range(len(base)))
        and sum(delta) == 0
    }))


_PROFILE_DATA = {
    "noisy_3x3_repeat6": {
        "canvas": (20, 14),
        "row_base": (5, 3, 5),
        "col_base": (5, 4, 3),
        "roles": (
            (0, 1, 2),
            (1, 3, 3),
            (4, 5, 0),
        ),
        "output_equality": (0, 1, 2, 3, 3, 1, 2, 4, 5),
        "role_count": 6,
    },
    "noisy_2x2_distinct4": {
        "canvas": (22, 11),
        "row_base": (6, 8),
        "col_base": (5, 3),
        "roles": (
            (0, 1),
            (2, 3),
        ),
        "output_equality": (0, 1, 2, 3),
        "role_count": 4,
    },
    "noisy_2x3_distinct6": {
        "canvas": (18, 19),
        "row_base": (5, 8),
        "col_base": (5, 5, 4),
        "roles": (
            (0, 1, 2),
            (3, 4, 5),
        ),
        "output_equality": (0, 1, 2, 3, 4, 5),
        "role_count": 6,
    },
    "noisy_4x3_repeat8": {
        "canvas": (22, 19),
        "row_base": (5, 4, 4, 3),
        "col_base": (3, 4, 6),
        "roles": (
            (0, 1, 2),
            (3, 4, 5),
            (3, 1, 6),
            (4, 4, 7),
        ),
        "output_equality": (0, 1, 2, 3, 4, 5, 6, 1, 5, 7, 4, 4),
        "role_count": 8,
    },
}

for _profile_data in _PROFILE_DATA.values():
    _profile_data["row_partitions"] = _nearby_partitions(
        _profile_data["row_base"]
    )
    _profile_data["col_partitions"] = _nearby_partitions(
        _profile_data["col_base"]
    )

_PROFILE_BY_CANVAS = {
    data["canvas"]: profile
    for profile, data in _PROFILE_DATA.items()
}

_PROFILE_INDEX = {
    profile: index
    for index, profile in enumerate(SCENE_PROFILES)
}


def _coerce_arc_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    first = grid[0]
    width = len(first) if isinstance(first, (list, tuple)) else 0
    if width == 0:
        return None, ["grid rows must be nonempty"]
    if len(grid) > 30 or width > 30:
        return None, ["grid dimensions must not exceed 30x30"]
    errors = []
    coerced = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted.append(0)
            else:
                converted.append(value)
        coerced.append(converted)
    if errors:
        return None, errors
    return coerced, []


def _components(grid):
    """Return same-color nonzero 4-components in reading order."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            queue = deque([(start_row, start_col)])
            seen.add((start_row, start_col))
            cells = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for delta_row, delta_col in (
                    (-1, 0),
                    (0, -1),
                    (0, 1),
                    (1, 0),
                ):
                    next_row = row + delta_row
                    next_col = col + delta_col
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        queue.append((next_row, next_col))
            rows = [row for row, _col in cells]
            cols = [col for _row, col in cells]
            result.append(
                {
                    "color": color,
                    "cells": tuple(cells),
                    "bbox": (
                        min(rows),
                        min(cols),
                        max(rows),
                        max(cols),
                    ),
                }
            )
    return result


def _rule_analysis(grid):
    """Analyze a grid with an independent Python mirror of the Racket rule."""
    retained = []
    for component in _components(grid):
        top, left, bottom, right = component["bbox"]
        if (bottom - top + 1) * (right - left + 1) > 2:
            retained.append(
                (
                    component["color"],
                    top,
                    left,
                    bottom,
                    right,
                )
            )
    if not retained:
        raise ValueError("grid has no retained nonzero object")

    row_breaks = tuple(sorted({
        coordinate
        for record in retained
        for coordinate in (record[1], record[3] + 1)
    }))
    col_breaks = tuple(sorted({
        coordinate
        for record in retained
        for coordinate in (record[2], record[4] + 1)
    }))
    row_groups = tuple(
        (row_breaks[index], row_breaks[index + 1] - 1)
        for index in range(len(row_breaks) - 1)
    )
    col_slots = tuple(
        (col_breaks[index], col_breaks[index + 1] - 1)
        for index in range(len(col_breaks) - 1)
    )
    if not row_groups or not col_slots:
        raise ValueError("retained objects do not define a slot grid")

    def covering_color(row_group, col_slot):
        row_start, row_end = row_group
        col_start, col_end = col_slot
        for color, top, left, bottom, right in retained:
            if (
                top <= row_start
                and bottom >= row_end
                and left <= col_start
                and right >= col_end
            ):
                return color
        return 0

    original = [
        [
            covering_color(row_group, col_slot)
            for col_slot in col_slots
        ]
        for row_group in row_groups
    ]
    output = [list(reversed(row)) for row in original]
    return {
        "retained": tuple(retained),
        "row_breaks": row_breaks,
        "col_breaks": col_breaks,
        "row_groups": row_groups,
        "col_slots": col_slots,
        "original": original,
        "output": output,
    }


def _equality_signature(grid):
    mapping = {}
    signature = []
    for row in grid:
        for value in row:
            if value not in mapping:
                mapping[value] = len(mapping)
            signature.append(mapping[value])
    return tuple(signature)


def _semantic_signature(grid):
    """Return the exact linked public profile represented by ``grid``."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    height = len(coerced)
    width = len(coerced[0])
    profile = _PROFILE_BY_CANVAS.get((height, width))
    if profile is None:
        return None
    data = _PROFILE_DATA[profile]
    try:
        analysis = _rule_analysis(coerced)
    except ValueError:
        return None

    output = analysis["output"]
    if (
        len(output) != len(data["roles"])
        or len(output[0]) != len(data["roles"][0])
        or any(value == 0 for row in output for value in row)
        or _equality_signature(output) != data["output_equality"]
    ):
        return None

    colors = {
        value
        for row in coerced
        for value in row
        if value != 0
    }
    if len(colors) != data["role_count"]:
        return None

    row_heights = tuple(
        end - start + 1
        for start, end in analysis["row_groups"]
    )
    col_widths = tuple(
        end - start + 1
        for start, end in analysis["col_slots"]
    )
    if (
        row_heights not in data["row_partitions"]
        or col_widths not in data["col_partitions"]
    ):
        return None

    row_breaks = analysis["row_breaks"]
    col_breaks = analysis["col_breaks"]
    top = row_breaks[0]
    bottom = row_breaks[-1]
    left = col_breaks[0]
    right = col_breaks[-1]
    if top < 1 or bottom >= height or left < 1 or right >= width:
        return None
    for row in range(height):
        for col in range(width):
            if not (top <= row < bottom and left <= col < right):
                if coerced[row][col] != 0:
                    return None

    holes = 0
    for row_index, (row_start, row_end) in enumerate(
        analysis["row_groups"]
    ):
        for col_index, (col_start, col_end) in enumerate(
            analysis["col_slots"]
        ):
            expected = analysis["original"][row_index][col_index]
            values = [
                coerced[row][col]
                for row in range(row_start, row_end + 1)
                for col in range(col_start, col_end + 1)
            ]
            if any(value not in (0, expected) for value in values):
                return None
            colored = sum(value == expected for value in values)
            if colored / len(values) < 0.65:
                return None
            holes += len(values) - colored
    if holes == 0:
        return None
    return {"scene_profile": profile}


def canonical_profile_index(grid):
    """Return the complete demonstrated profile index, if calibrated."""
    signature = _semantic_signature(grid)
    if signature is None:
        return None
    return _PROFILE_INDEX[signature["scene_profile"]]


def observe_overrides(grid):
    """Recover every declared exact axis from a valid returned grid."""
    signature = _semantic_signature(grid)
    return {} if signature is None else dict(signature)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    if (
        "scene_profile" in overrides
        and overrides["scene_profile"] not in SCENE_PROFILES
    ):
        raise ValueError("unknown scene_profile")


def _connected_and_spans(cells, top, left, bottom, right):
    if not cells:
        return False
    if not (
        any(row == top for row, _col in cells)
        and any(row == bottom for row, _col in cells)
        and any(col == left for _row, col in cells)
        and any(col == right for _row, col in cells)
    ):
        return False
    start = next(iter(cells))
    queue = deque([start])
    reached = {start}
    while queue:
        row, col = queue.popleft()
        for delta_row, delta_col in (
            (-1, 0),
            (0, -1),
            (0, 1),
            (1, 0),
        ):
            candidate = (row + delta_row, col + delta_col)
            if candidate in cells and candidate not in reached:
                reached.add(candidate)
                queue.append(candidate)
    return len(reached) == len(cells)


def _carved_cells(top, left, height, width, desired_holes, rng):
    """Carve noise while retaining one connected full-bbox component."""
    bottom = top + height - 1
    right = left + width - 1
    full = {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    }
    best = full
    for _attempt in range(8):
        cells = set(full)
        spine_row = rng.randint(top, bottom)
        spine_col = rng.randint(left, right)
        protected = {
            (spine_row, col)
            for col in range(left, right + 1)
        } | {
            (row, spine_col)
            for row in range(top, bottom + 1)
        }
        candidates = list(full - protected)
        rng.shuffle(candidates)
        for candidate in candidates:
            if len(full) - len(cells) >= desired_holes:
                break
            cells.remove(candidate)
            if not _connected_and_spans(
                cells,
                top,
                left,
                bottom,
                right,
            ):
                cells.add(candidate)
        if len(cells) < len(best):
            best = cells
        if len(full) - len(cells) >= desired_holes:
            return cells
    return best


def _hole_targets(row_heights, col_widths, difficulty, rng):
    maximum_fraction = {
        "easy": 0.14,
        "hard": 0.32,
    }.get(difficulty, 0.23)
    targets = []
    for row_height in row_heights:
        row_targets = []
        for col_width in col_widths:
            area = row_height * col_width
            density_limit = area - ((65 * area + 99) // 100)
            maximum = min(
                density_limit,
                max(1, round(area * maximum_fraction)),
            )
            row_targets.append(rng.randint(0, maximum))
        targets.append(row_targets)
    if not any(value for row in targets for value in row):
        targets[0][0] = 1
    return targets


def _construct_scene(
    profile,
    role_colors,
    row_heights,
    col_widths,
    top,
    left,
    difficulty,
    rng,
):
    data = _PROFILE_DATA[profile]
    height, width = data["canvas"]
    grid = [
        [0 for _col in range(width)]
        for _row in range(height)
    ]
    hole_targets = _hole_targets(
        row_heights,
        col_widths,
        difficulty,
        rng,
    )
    row_start = top
    for row_index, row_height in enumerate(row_heights):
        col_start = left
        for col_index, col_width in enumerate(col_widths):
            role = data["roles"][row_index][col_index]
            color = role_colors[role]
            cells = _carved_cells(
                row_start,
                col_start,
                row_height,
                col_width,
                hole_targets[row_index][col_index],
                rng,
            )
            for row, col in cells:
                grid[row][col] = color
            col_start += col_width
        row_start += row_height
    return grid


def _fallback_scene(profile, role_colors):
    """Construct a deterministic complete profile without random retries."""
    data = _PROFILE_DATA[profile]
    height, width = data["canvas"]
    grid = [
        [0 for _col in range(width)]
        for _row in range(height)
    ]
    row_start = 1
    for row_index, row_height in enumerate(data["row_base"]):
        col_start = 1
        for col_index, col_width in enumerate(data["col_base"]):
            color = role_colors[data["roles"][row_index][col_index]]
            for row in range(row_start, row_start + row_height):
                for col in range(col_start, col_start + col_width):
                    grid[row][col] = color
            grid[
                row_start + row_height // 2
            ][
                col_start + col_width // 2
            ] = 0
            col_start += col_width
        row_start += row_height
    if _semantic_signature(grid) != {"scene_profile": profile}:
        raise AssertionError("complete fallback lost its scene profile")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    data = _PROFILE_DATA[profile]
    role_colors = ctx.draw_distinct_colors(
        "role_colors",
        n=data["role_count"],
        exclude={0},
    )
    layout_rng = ctx.draw_rng("layout")
    row_heights = layout_rng.choice(data["row_partitions"])
    col_widths = layout_rng.choice(data["col_partitions"])
    core_height = sum(row_heights)
    core_width = sum(col_widths)
    height, width = data["canvas"]
    top = layout_rng.randint(1, height - core_height - 1)
    left = layout_rng.randint(1, width - core_width - 1)
    grid = _construct_scene(
        profile,
        role_colors,
        row_heights,
        col_widths,
        top,
        left,
        difficulty,
        ctx.draw_rng("noise"),
    )
    if _semantic_signature(grid) != {"scene_profile": profile}:
        grid = _fallback_scene(profile, role_colors)
    if observe_overrides(grid) != {"scene_profile": profile}:
        raise AssertionError("constructed scene lost its exact axis")
    return grid


def rule_mirror(grid):
    """Broad, input-pure Python mirror of the canonical Racket rule."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    analysis = _rule_analysis(coerced)
    return [row[:] for row in analysis["output"]]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept only complete calibrated noisy slot-grid profiles."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return errors
    if _semantic_signature(coerced) is None:
        return [
            "grid must be one complete demonstrated noisy slot-grid profile "
            "with its exact canvas, partition family, repeated-color pattern, "
            "zero margin, per-slot coverage, and at least one interior hole"
        ]
    return []
