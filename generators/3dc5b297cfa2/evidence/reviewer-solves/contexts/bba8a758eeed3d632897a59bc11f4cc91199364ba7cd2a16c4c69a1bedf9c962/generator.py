"""Constructive generator for ARC task fc4aaf52 / generator 3dc5b297cfa2.

Authority rule
--------------
Treat the unique modal color as background and the remaining cells as one
connected two-color shape. Swap the two shape colors everywhere. The top half
of the shape's bounding box (inclusive of its floor midpoint) moves right;
the bottom half stays in place. The ordinary shift is the full shape-bounding-
box width. When black (0) is one of the shape colors, the shift is instead the
horizontal span of the non-black shape cells.

The six-slot curriculum repeats a black/black/non-black branch pattern. Every
sliding two-demo lesson therefore contains a black witness, and every
three-pair lesson still contains one after any single query holdout. Four slots
reproduce the linked 16x16 canonical profiles; two black slots broaden
dimensions and colors by difficulty.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]

GENERATOR_ID = "3dc5b297cfa2"
TASK_ID = GENERATOR_ID
VERSION = "3.1.1"
RULE_HASH = "69b3b2d19383"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.60

SUMMARY = (
    "One connected two-color shape sits on a unique nonzero modal background. "
    "Swap the two shape colors. Keep the bottom half in place and shift the "
    "top half right by the full shape-bbox width; when black (0) is a shape "
    "color, use the horizontal span of the non-black cells instead. The "
    "default six-slot schedule uses a repeating black/black/nonblack pattern, "
    "includes all linked 16x16 canonical bbox profiles, and keeps a black-branch "
    "witness after any one query holdout from a three-pair lesson. Every two-demo "
    "lesson refutes full-width, no-swap, move-both-halves, and grid-midpoint shortcuts."
)

INVARIANTS = [
    "grid is rectangular with literal ARC colors 0..9",
    "the unique modal background is nonzero",
    "exactly two non-background colors form one 4-connected shape",
    "shape bbox is 4..8 rows by 3..7 columns",
    "both bbox halves contain both shape colors",
    "all top-half translated cells remain inside the grid",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "six-slot canonical/broad schedule",
        "valid": "12..20",
    },
    "grid_w": {
        "type": "int",
        "default": "six-slot canonical/broad schedule",
        "valid": "16..24",
    },
    "bbox_h": {
        "type": "int",
        "default": "six-slot canonical/broad schedule",
        "valid": "4..8",
    },
    "bbox_w": {
        "type": "int",
        "default": "six-slot canonical/broad schedule",
        "valid": "3..7",
    },
    "background_color": {
        "type": "int",
        "default": "canonical 8 or broad keyed draw",
        "valid": "1..9",
    },
    "black_shape": {
        "type": "bool",
        "default": "black/black/nonblack six-slot schedule",
        "valid": "true|false",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (
    "canonical_black_8x5",
    "broad_black",
    "canonical_nonblack_8x5",
    "canonical_black_8x5",
    "broad_black",
    "canonical_nonblack_6x7",
)
_ALLOWED_DIFFICULTIES = {None, "easy", "medium", "hard"}


def _validate_call(seed: Any, sample_index: Any, difficulty: Any) -> None:
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer (not bool), got {type(seed).__name__}")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    if type(sample_index) is not int:
        raise TypeError(
            "sample_index must be an integer (not bool), "
            f"got {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


_CANONICAL_DEFAULTS: dict[str, dict[str, object]] = {
    "canonical_black_8x5": {
        "grid_h": 16,
        "grid_w": 16,
        "bbox_h": 8,
        "bbox_w": 5,
        "background_color": 8,
        "black_shape": True,
    },
    "canonical_nonblack_8x5": {
        "grid_h": 16,
        "grid_w": 16,
        "bbox_h": 8,
        "bbox_w": 5,
        "background_color": 8,
        "black_shape": False,
    },
    "canonical_nonblack_6x7": {
        "grid_h": 16,
        "grid_w": 16,
        "bbox_h": 6,
        "bbox_w": 7,
        "background_color": 8,
        "black_shape": False,
    },
}


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the declared six-slot teaching profile.

    The slot depends only on sample_index. The branch pattern is B,B,N,B,B,N,
    so every consecutive two-example window includes a black witness and every
    consecutive three-example window retains one after any single holdout.
    """
    _validate_call(seed, sample_index, difficulty)
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _scheduled_defaults(seed: int, sample_index: int, difficulty: Any) -> dict[str, object]:
    profile = schedule_profile(seed, sample_index, difficulty)
    if profile in _CANONICAL_DEFAULTS:
        return dict(_CANONICAL_DEFAULTS[profile])
    # The broad slots are always the black branch but leave every numeric/color
    # axis to a keyed, difficulty-aware draw. This broadens support without
    # creating a rotated three-pair lesson that can hide the special branch.
    return {"black_shape": True}


def _normalize_grid(grid: Any) -> tuple[Grid | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None, ["grid must be rectangular"]

    normalized: Grid = []
    for row_index, row in enumerate(grid):
        normalized_row: list[int] = []
        for column_index, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return None, [
                    f"cell ({row_index},{column_index}) is not a literal ARC color 0..9: {value!r}"
                ]
            normalized_row.append(value)
        normalized.append(normalized_row)
    return normalized, []


def _mode_info(grid: Sequence[Sequence[int]]) -> tuple[int, Counter[int], bool]:
    counts: Counter[int] = Counter(value for row in grid for value in row)
    ordered = counts.most_common()
    background = ordered[0][0]
    unique = len(ordered) == 1 or ordered[0][1] > ordered[1][1]
    return background, counts, unique


def _shape_cells(
    grid: Sequence[Sequence[int]], background: int
) -> list[tuple[int, int, int]]:
    return [
        (row, column, value)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value != background
    ]


def _bbox(cells: Sequence[tuple[int, int, int]]) -> tuple[int, int, int, int]:
    return (
        min(row for row, _column, _value in cells),
        max(row for row, _column, _value in cells),
        min(column for _row, column, _value in cells),
        max(column for _row, column, _value in cells),
    )


def _component_count(cells: Sequence[tuple[int, int, int]]) -> int:
    remaining = {(row, column) for row, column, _value in cells}
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            row, column = stack.pop()
            for neighbor in (
                (row - 1, column),
                (row + 1, column),
                (row, column - 1),
                (row, column + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return count


def _analysis(grid: Any) -> dict[str, Any]:
    normalized, errors = _normalize_grid(grid)
    if errors:
        raise ValueError("cannot analyze malformed grid: " + "; ".join(errors))
    assert normalized is not None
    background, counts, unique_mode = _mode_info(normalized)
    cells = _shape_cells(normalized, background)
    if not cells:
        raise ValueError("cannot analyze a grid with no non-background cells")
    rmin, rmax, cmin, cmax = _bbox(cells)
    shape_colors = list(dict.fromkeys(value for _row, _column, value in cells))
    nonblack = [cell for cell in cells if cell[2] != 0]
    if 0 in shape_colors and not nonblack:
        raise ValueError("black branch has no non-black shape cells")
    shift = (
        max(column for _row, column, _value in nonblack)
        - min(column for _row, column, _value in nonblack)
        + 1
        if 0 in shape_colors
        else cmax - cmin + 1
    )
    return {
        "grid": normalized,
        "height": len(normalized),
        "width": len(normalized[0]),
        "background": background,
        "counts": counts,
        "unique_mode": unique_mode,
        "cells": cells,
        "shape_colors": shape_colors,
        "rmin": rmin,
        "rmax": rmax,
        "cmin": cmin,
        "cmax": cmax,
        "rmid": (rmin + rmax) // 2,
        "bbox_h": rmax - rmin + 1,
        "bbox_w": cmax - cmin + 1,
        "shift": shift,
    }


def observe_overrides(grid: Any) -> dict[str, object]:
    """Recover every declared exact axis from pixels alone."""
    info = _analysis(grid)
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "bbox_h": info["bbox_h"],
        "bbox_w": info["bbox_w"],
        "background_color": info["background"],
        "black_shape": 0 in info["shape_colors"],
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Validate the authority-compatible input grammar and exact overrides."""
    del difficulty
    normalized, errors = _normalize_grid(grid)
    if errors:
        return errors
    assert normalized is not None

    height, width = len(normalized), len(normalized[0])
    if not 12 <= height <= 20:
        errors.append(f"height {height} outside declared envelope 12..20")
    if not 16 <= width <= 24:
        errors.append(f"width {width} outside declared envelope 16..24")

    background, counts, unique_mode = _mode_info(normalized)
    if not unique_mode:
        errors.append(f"background mode is not unique: counts={dict(counts)}")
    if background == 0:
        errors.append("background must be nonzero so black can be an observable shape color")

    cells = _shape_cells(normalized, background)
    if not cells:
        errors.append("expected one nonempty shape")
        return errors
    shape_colors = set(value for _row, _column, value in cells)
    if len(shape_colors) != 2:
        errors.append(
            f"expected exactly two shape colors distinct from background, found {sorted(shape_colors)}"
        )
    if len(counts) != 3:
        errors.append(f"expected total palette size 3, found {len(counts)}")

    rmin, rmax, cmin, cmax = _bbox(cells)
    bbox_h = rmax - rmin + 1
    bbox_w = cmax - cmin + 1
    if not 4 <= bbox_h <= 8:
        errors.append(f"shape bbox height {bbox_h} outside 4..8")
    if not 3 <= bbox_w <= 7:
        errors.append(f"shape bbox width {bbox_w} outside 3..7")
    components = _component_count(cells)
    if components != 1:
        errors.append(f"shape must be one 4-connected component, found {components}")

    if len(shape_colors) == 2:
        rmid = (rmin + rmax) // 2
        top_colors = {value for row, _column, value in cells if row <= rmid}
        bottom_colors = {value for row, _column, value in cells if row > rmid}
        if top_colors != shape_colors:
            errors.append("top bbox half must contain both shape colors")
        if bottom_colors != shape_colors:
            errors.append("bottom bbox half must contain both shape colors")

        if 0 in shape_colors:
            nonblack = [cell for cell in cells if cell[2] != 0]
            if not nonblack:
                errors.append("black branch must contain non-black shape cells")
                shift = 0
            else:
                shift = (
                    max(column for _row, column, _value in nonblack)
                    - min(column for _row, column, _value in nonblack)
                    + 1
                )
            if shift >= bbox_w:
                errors.append(
                    "black branch must expose a non-black span narrower than the full bbox"
                )
        else:
            shift = bbox_w

        if any(column + shift >= width for row, column, _value in cells if row <= rmid):
            errors.append("top-half translation would leave the grid")

    requested = ((meta or {}).get("overrides") or {}) if isinstance(meta, dict) else {}
    if requested and not errors:
        observed = observe_overrides(normalized)
        for key, value in requested.items():
            if key in AXES and observed.get(key) != value:
                errors.append(
                    f"override {key} requested {value!r}, observed {observed.get(key)!r}"
                )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Accept the three linked empirical canonical profiles exactly."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    observed = observe_overrides(grid)
    signature = (
        observed["grid_h"],
        observed["grid_w"],
        observed["bbox_h"],
        observed["bbox_w"],
        observed["background_color"],
        observed["black_shape"],
    )
    linked = {
        (16, 16, 8, 5, 8, True),
        (16, 16, 8, 5, 8, False),
        (16, 16, 6, 7, 8, False),
    }
    if signature not in linked:
        reasons.append(f"linked canonical signature not observed: {signature!r}")
    return reasons


def _transform(
    grid: Sequence[Sequence[int]],
    *,
    force_full_bbox_shift: bool = False,
    swap_colors: bool = True,
    move_bottom: bool = False,
    use_grid_midpoint: bool = False,
) -> Grid:
    info = _analysis(grid)
    shape_colors = info["shape_colors"]
    if len(shape_colors) != 2:
        raise ValueError(f"rule requires exactly two shape colors, got {shape_colors!r}")
    first, second = shape_colors
    shift = info["bbox_w"] if force_full_bbox_shift else info["shift"]
    split = (info["height"] - 1) // 2 if use_grid_midpoint else info["rmid"]
    output = full_grid(info["height"], info["width"], info["background"])
    for row, column, value in info["cells"]:
        new_value = second if value == first else first
        if not swap_colors:
            new_value = value
        if row <= split or move_bottom:
            new_column = column + shift
            if 0 <= new_column < info["width"]:
                output[row][new_column] = new_value
        else:
            output[row][column] = new_value
    return output


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    """Independent Python mirror used by tests; canonical Racket is authority."""
    return _transform(grid)


def _rival_full_bbox_shift(grid: Sequence[Sequence[int]]) -> Grid:
    return _transform(grid, force_full_bbox_shift=True)


def _rival_no_color_swap(grid: Sequence[Sequence[int]]) -> Grid:
    return _transform(grid, swap_colors=False)


def _rival_move_both_halves(grid: Sequence[Sequence[int]]) -> Grid:
    return _transform(grid, move_bottom=True)


def _rival_grid_midpoint(grid: Sequence[Sequence[int]]) -> Grid:
    return _transform(grid, use_grid_midpoint=True)


def _black_span_exception_witness(grid: Sequence[Sequence[int]]) -> bool:
    info = _analysis(grid)
    return 0 in info["shape_colors"] and info["shift"] < info["bbox_w"]


def _color_swap_witness(grid: Sequence[Sequence[int]]) -> bool:
    return _rival_no_color_swap(grid) != rule_mirror(grid)


def _stationary_bottom_witness(grid: Sequence[Sequence[int]]) -> bool:
    return _rival_move_both_halves(grid) != rule_mirror(grid)


def _shape_midpoint_witness(grid: Sequence[Sequence[int]]) -> bool:
    return _rival_grid_midpoint(grid) != rule_mirror(grid)


SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], Grid]] = {
    "always_full_bbox_shift": _rival_full_bbox_shift,
    "no_color_swap": _rival_no_color_swap,
    "move_both_halves": _rival_move_both_halves,
    "split_at_grid_midpoint": _rival_grid_midpoint,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS

SEMANTIC_WITNESSES: dict[str, Callable[[Sequence[Sequence[int]]], bool]] = {
    "black_nonzero_span_exception": _black_span_exception_witness,
    "color_swap_is_visible": _color_swap_witness,
    "bottom_stays_in_place": _stationary_bottom_witness,
    "shape_not_grid_midpoint": _shape_midpoint_witness,
}
WITNESS_RIVALS = {
    "black_nonzero_span_exception": ["always_full_bbox_shift"],
    "color_swap_is_visible": ["no_color_swap"],
    "bottom_stays_in_place": ["move_both_halves"],
    "shape_not_grid_midpoint": ["split_at_grid_midpoint"],
}


def lesson_identifiable(
    demos: Sequence[dict[str, Any]], query: dict[str, Any]
) -> list[str]:
    """Require a two-demo window to eliminate every declared shortcut."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations, got {len(demos)}"]

    for index, pair in enumerate(demos):
        if "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} lacks input/output")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the pinned rule")

    if "input" not in query:
        reasons.append("query lacks input")
    else:
        query_errors = self_check(query["input"])
        if query_errors:
            reasons.append("query input is outside the generator grammar: " + "; ".join(query_errors))

    for name, rival in LESSON_COMPETITORS.items():
        if not any(
            "input" in pair
            and "output" in pair
            and rival(pair["input"]) != pair["output"]
            for pair in demos
        ):
            reasons.append(f"competitor {name!r} survives every demonstration")
    return reasons


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    bounds = {
        "grid_h": (12, 20),
        "grid_w": (16, 24),
        "bbox_h": (4, 8),
        "bbox_w": (3, 7),
        "background_color": (1, 9),
    }
    for name, (lo, hi) in bounds.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"override {name!r} must be an int, got {value!r}")
        if not lo <= value <= hi:
            raise ValueError(f"override {name!r}={value} outside [{lo}, {hi}]")
    if "black_shape" in overrides and overrides["black_shape"] is not None:
        value = overrides["black_shape"]
        if type(value) is not bool:
            raise TypeError(f"override 'black_shape' must be bool, got {value!r}")


def _row_insets(height: int, width: int, rounded: bool) -> list[int]:
    cap = (width - 1) // 2
    if rounded and cap > 1:
        cap -= 1
    if height == 1:
        return [0]
    insets = [
        min(cap, round(cap * abs(2 * row - (height - 1)) / (height - 1)))
        for row in range(height)
    ]
    # Rounding can otherwise taper both middle rows of a short/wide even-height
    # silhouette (e.g. 4x7), silently shrinking the realized bounding box.
    # Pin the central row pair to full width so every declared bbox_w override
    # is directly observable from pixels.
    insets[(height - 1) // 2] = 0
    insets[height // 2] = 0
    return insets


def _paint_shape(
    *,
    height: int,
    width: int,
    first: int,
    second: int,
    black_shape: bool,
    rounded: bool,
    phase: int,
) -> list[tuple[int, int, int]]:
    """Return local (row, col, color) cells for one connected silhouette."""
    insets = _row_insets(height, width, rounded)
    positions: list[tuple[int, int]] = []
    row_positions: dict[int, list[int]] = {}
    for row, inset in enumerate(insets):
        columns = list(range(inset, width - inset))
        row_positions[row] = columns
        positions.extend((row, column) for column in columns)

    colors: dict[tuple[int, int], int] = {}
    if black_shape:
        # Endpoints of every occupied row are black. Non-black cells remain
        # strictly inside the full bbox, so their horizontal span is visibly
        # narrower than bbox width and the special shift branch is identifiable.
        for row, columns in row_positions.items():
            for column in columns:
                colors[(row, column)] = (
                    first if column in (columns[0], columns[-1]) else second
                )
    else:
        for row, column in positions:
            colors[(row, column)] = first if (row + column + phase) % 2 == 0 else second

    split = (height - 1) // 2
    halves = (
        [position for position in positions if position[0] <= split],
        [position for position in positions if position[0] > split],
    )
    for half in halves:
        if black_shape:
            interior = [position for position in half if 0 < position[1] < width - 1]
            endpoints = [
                position
                for position in half
                if position[1] in (row_positions[position[0]][0], row_positions[position[0]][-1])
            ]
            if not interior or not endpoints:
                raise AssertionError("silhouette cannot expose both black-branch colors in each half")
            colors[interior[0]] = second
            colors[endpoints[0]] = first
        else:
            if len(half) < 2:
                raise AssertionError("silhouette half too small for two colors")
            colors[half[0]] = first
            colors[half[1]] = second

    return [(row, column, colors[(row, column)]) for row, column in positions]


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> Grid:
    _validate_call(seed, sample_index, difficulty)
    _validate_overrides(overrides)

    effective = dict(overrides)
    for key, value in _scheduled_defaults(seed, sample_index, difficulty).items():
        effective.setdefault(key, value)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    height = ctx.draw_int_diff("grid_h", 12, 20)
    width = ctx.draw_int_diff("grid_w", 16, 24)
    bbox_h = ctx.draw_int_diff("bbox_h", 4, 8)
    bbox_w = ctx.draw_int_diff("bbox_w", 3, 7)
    background = ctx.draw_choice("background_color", tuple(range(1, 10)))
    black_shape = ctx.draw_choice("black_shape", (False, True))

    if black_shape:
        first = 0
        second = ctx.draw_color("nonblack_shape_color", exclude={0, background})
    else:
        first, second = ctx.draw_distinct_colors(
            "shape_colors", n=2, exclude={0, background}
        )

    placement_rng = ctx.draw_rng("placement")
    shape_rng = ctx.draw_rng("silhouette")
    color_rng = ctx.draw_rng("color_phase")

    legal_rows = list(range(1, height - bbox_h))
    grid_midpoint = (height - 1) // 2
    informative_rows = [
        row
        for row in legal_rows
        if row + (bbox_h - 1) // 2 != grid_midpoint
    ]
    if not informative_rows:
        raise AssertionError("declared envelopes left no shape-vs-grid midpoint witness")
    top = placement_rng.choice(informative_rows)

    max_left = width - 2 * bbox_w - 1
    if max_left < 1:
        raise AssertionError(
            f"declared envelopes cannot fit bbox width {bbox_w} and full shift in width {width}"
        )
    left = placement_rng.randint(1, max_left)

    local_cells = _paint_shape(
        height=bbox_h,
        width=bbox_w,
        first=first,
        second=second,
        black_shape=black_shape,
        rounded=bool(shape_rng.randrange(2)),
        phase=color_rng.randrange(2),
    )
    grid = full_grid(height, width, background)
    for row, column, value in local_cells:
        grid[top + row][left + column] = value

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError("generator produced invalid scene: " + "; ".join(errors))

    missing = [name for name, predicate in SEMANTIC_WITNESSES.items() if not predicate(grid)]
    # Only the black-span witness is branch-specific. All other witnesses must
    # fire on every ordinary draw; black slots must fire all four.
    permitted = set() if black_shape else {"black_nonzero_span_exception"}
    unexpected = [name for name in missing if name not in permitted]
    if unexpected:
        raise AssertionError("generator hid required semantic witness(es): " + ", ".join(unexpected))
    return grid
