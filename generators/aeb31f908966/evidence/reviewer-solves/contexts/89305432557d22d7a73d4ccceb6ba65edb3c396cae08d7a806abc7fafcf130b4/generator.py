"""Canonical-aligned generator for ARC task aeb31f908966.

A single color-2 marker selects a reflection axis: a top-edge marker selects
its column, while a left-edge marker selects its row.  Every color-5 source is
reflected across that axis.  The reflected cell becomes color 7 only when the
target is in bounds and currently background.

The six-profile production schedule deliberately teaches all semantically
important branches: both marker orientations, source cells on both sides,
occupied mirror targets, and out-of-bounds mirror targets.  Every public axis
is exact, constructive, and recoverable from the returned input grid.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "aeb31f908966"
TASK_ID = "aeb31f908966"
VERSION = "4.0.0"
RULE_HASH = "efb0a4280598"

SUMMARY = (
    "A 0-background grid has one red (2) marker on the top or left edge and "
    "a gray (5) object. The marker selects a vertical or horizontal mirror "
    "axis. In-bounds reflections onto background become orange (7); occupied "
    "or out-of-bounds targets are left unchanged. A six-profile curriculum "
    "covers both orientations, both source sides, occupied targets, and "
    "out-of-bounds targets."
)

EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 6

INVARIANTS = [
    "grid size is 10..16 rows by 10..16 columns",
    "exactly one color-2 marker lies on the top or left edge, never the corner",
    "there are 3..8 color-5 cells and none lies on the selected axis",
    "at least one color-5 cell has an in-bounds empty reflection target",
    "only colors 0, 2, and 5 occur in generator inputs",
]

AXES = {
    "grid_h": {"type": "int", "default": "six-profile schedule", "valid": "10..16"},
    "grid_w": {"type": "int", "default": "six-profile schedule", "valid": "10..16"},
    "orientation": {"type": "str", "default": "six-profile schedule", "valid": "top|left"},
    "shape_side": {"type": "str", "default": "six-profile schedule", "valid": "negative|positive"},
    "n_5cells": {"type": "int", "default": "difficulty-aware", "valid": "3..8"},
    "edge_case": {"type": "str", "default": "six-profile schedule", "valid": "clean|occupied|out_of_bounds"},
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

# name, final height, final width, orientation, majority source side, edge case
_PROFILE_SPECS = (
    ("top_negative_clean_11x11", 11, 11, "top", "negative", "clean"),
    ("top_positive_occupied_10x12", 10, 12, "top", "positive", "occupied"),
    ("left_negative_clean_12x10", 12, 10, "left", "negative", "clean"),
    ("left_positive_occupied_12x12", 12, 12, "left", "positive", "occupied"),
    ("top_negative_oob_11x11", 11, 11, "top", "negative", "out_of_bounds"),
    ("left_positive_oob_12x12", 12, 12, "left", "positive", "out_of_bounds"),
)
SCHEDULE_PROFILES = tuple(spec[0] for spec in _PROFILE_SPECS)

_ALLOWED_DIFFICULTIES = {None, "easy", "medium", "hard"}
_INT_RANGES = {"grid_h": (10, 16), "grid_w": (10, 16), "n_5cells": (3, 8)}
_STR_OPTIONS = {
    "orientation": ("top", "left"),
    "shape_side": ("negative", "positive"),
    "edge_case": ("clean", "occupied", "out_of_bounds"),
}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
Grid = list[list[int]]


def _validate_seed_index(seed: int, sample_index: int) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")


def _validate_difficulty(difficulty: str | None) -> None:
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise KeyError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name, value in overrides.items():
        if name in _INT_RANGES:
            if type(value) is not int:
                raise TypeError(f"{name} override must be an integer (not bool)")
            lo, hi = _INT_RANGES[name]
            if not lo <= value <= hi:
                raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")
        else:
            if type(value) is not str:
                raise TypeError(f"{name} override must be a string")
            if value not in _STR_OPTIONS[name]:
                legal = "|".join(_STR_OPTIONS[name])
                raise ValueError(f"{name} override {value!r} not in {legal}")


def _profile_spec(sample_index: int) -> tuple[str, int, int, str, str, str]:
    return _PROFILE_SPECS[sample_index % LESSON_SCHEDULE_PERIOD]


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """Return the deterministic profile name for this production index."""
    _validate_seed_index(seed, sample_index)
    _validate_difficulty(difficulty)
    return _profile_spec(sample_index)[0]


def _scheduled_choice(ctx, label: str, options: Sequence[Any], target: Any) -> Any:
    """Expose the full legal domain while making the scheduled default exact."""
    arranged = list(options)
    selected_index = ctx.draw_rng(label).randrange(len(arranged))
    target_index = arranged.index(target)
    arranged[selected_index], arranged[target_index] = arranged[target_index], arranged[selected_index]
    return ctx.draw_choice(label, arranged)


def _scheduled_int(ctx, label: str, lo: int, hi: int, target: int) -> int:
    return int(_scheduled_choice(ctx, label, tuple(range(lo, hi + 1)), target))


def _transpose(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid)]


def _grow_shape(
    rng,
    count: int,
    height: int,
    allowed_cols: Iterable[int],
    *,
    initial: Iterable[tuple[int, int]] = (),
) -> list[tuple[int, int]]:
    """Grow a deterministic connected set, never using marker row zero."""
    allowed = {
        (row, col)
        for row in range(1, height)
        for col in sorted(set(allowed_cols))
    }
    if len(allowed) < count:
        raise ValueError(f"shape domain has {len(allowed)} cells, need {count}")
    cells = set(initial)
    if not cells:
        cells.add(rng.choice(sorted(allowed)))
    if not cells <= allowed:
        raise ValueError("initial shape cells fall outside the allowed domain")
    while len(cells) < count:
        frontier = sorted(
            {
                (row + dr, col + dc)
                for row, col in cells
                for dr, dc in _CARDINAL
                if (row + dr, col + dc) in allowed and (row + dr, col + dc) not in cells
            }
        )
        choices = frontier if frontier else sorted(allowed - cells)
        cells.add(rng.choice(choices))
    return sorted(cells)


def _axis_for(width: int, shape_side: str, edge_case: str, rng) -> int:
    if edge_case == "out_of_bounds":
        return width - 3 if shape_side == "negative" else 2
    candidates = list(range(3, width - 3))
    if not candidates:
        raise ValueError(f"width {width} leaves no central reflection axis")
    return rng.choice(candidates)


def _side_columns(width: int, axis: int, shape_side: str, edge_case: str) -> list[int]:
    sign = -1 if shape_side == "negative" else 1
    if edge_case == "out_of_bounds":
        distances = (1, 2, 3)
    else:
        max_distance = min(axis, width - 1 - axis)
        distances = range(1, max_distance + 1)
    return [axis + sign * distance for distance in distances]


def _draw_top_oriented(
    height: int,
    width: int,
    shape_side: str,
    n_5cells: int,
    edge_case: str,
    axis_rng,
    shape_rng,
) -> Grid:
    axis = _axis_for(width, shape_side, edge_case, axis_rng)
    allowed_cols = _side_columns(width, axis, shape_side, edge_case)
    grid = full_grid(height, width, 0)

    if edge_case == "out_of_bounds":
        sign = -1 if shape_side == "negative" else 1
        anchor_row = shape_rng.randint(2, height - 3)
        initial = [(anchor_row, axis + sign * distance) for distance in (1, 2, 3)]
        sources = _grow_shape(
            shape_rng,
            n_5cells,
            height,
            allowed_cols,
            initial=initial,
        )
    elif edge_case == "occupied":
        primary = _grow_shape(shape_rng, n_5cells - 1, height, allowed_cols)
        blocked_source = shape_rng.choice(primary)
        blocked_target = (blocked_source[0], 2 * axis - blocked_source[1])
        sources = sorted(primary + [blocked_target])
    else:
        sources = _grow_shape(shape_rng, n_5cells, height, allowed_cols)

    for row, col in sources:
        grid[row][col] = 5
    grid[0][axis] = 2
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_seed_index(seed, sample_index)
    _validate_difficulty(difficulty)
    _validate_overrides(overrides)

    _name, target_h, target_w, target_orientation, target_side, target_edge = _profile_spec(sample_index)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    final_h = _scheduled_int(ctx, "grid_h", 10, 16, target_h)
    final_w = _scheduled_int(ctx, "grid_w", 10, 16, target_w)
    orientation = str(
        _scheduled_choice(ctx, "orientation", _STR_OPTIONS["orientation"], target_orientation)
    )
    shape_side = str(
        _scheduled_choice(ctx, "shape_side", _STR_OPTIONS["shape_side"], target_side)
    )
    n_5cells = ctx.draw_int_diff("n_5cells", 3, 8)
    edge_case = str(
        _scheduled_choice(ctx, "edge_case", _STR_OPTIONS["edge_case"], target_edge)
    )

    # Build the vertical-axis form first. Transposition maps a top marker to a
    # left marker while preserving negative/positive side semantics.
    base_h, base_w = (final_h, final_w) if orientation == "top" else (final_w, final_h)
    grid = _draw_top_oriented(
        base_h,
        base_w,
        shape_side,
        n_5cells,
        edge_case,
        ctx.draw_rng("axis_position"),
        ctx.draw_rng("shape_layout"),
    )
    return grid if orientation == "top" else _transpose(grid)


def _validate_rectangular_grid(grid: object) -> tuple[list[str], int, int]:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid must be a non-empty list of rows"], 0, 0
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be non-empty and rectangular"], len(grid), width
    errors: list[str] = []
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell ({row},{col}) must be an integer ARC color 0..9")
    return errors, len(grid), width


def _chosen_axis(grid: Grid) -> tuple[str, int]:
    height, width = len(grid), len(grid[0])
    top = [col for col in range(width) if grid[0][col] == 2]
    left = [row for row in range(1, height) if grid[row][0] == 2]
    if len(top) + len(left) != 1:
        raise ValueError("expected exactly one top- or left-edge marker")
    return ("top", top[0]) if top else ("left", left[0])


def _mirror(orientation: str, axis: int, row: int, col: int) -> tuple[int, int]:
    if orientation == "top":
        return row, 2 * axis - col
    return 2 * axis - row, col


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the lawful input manifold, including a non-identity outcome."""
    errors, height, width = _validate_rectangular_grid(grid)
    if errors:
        return errors
    if not 10 <= height <= 16:
        errors.append(f"height {height} outside 10..16")
    if not 10 <= width <= 16:
        errors.append(f"width {width} outside 10..16")

    colors = {value for row in grid for value in row}
    illegal = sorted(colors - {0, 2, 5})
    if illegal:
        errors.append(f"input contains colors outside 0,2,5: {illegal}")
    marker_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]
    if len(marker_cells) != 1:
        errors.append(f"expected exactly one color-2 marker, got {len(marker_cells)}")
        return errors
    marker_row, marker_col = marker_cells[0]
    if marker_row == 0 and marker_col == 0:
        errors.append("marker may not occupy the top-left corner")
        return errors
    if marker_row != 0 and marker_col != 0:
        errors.append("marker must lie on the top or left edge")
        return errors
    orientation, axis = ("top", marker_col) if marker_row == 0 else ("left", marker_row)

    fives = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    if not 3 <= len(fives) <= 8:
        errors.append(f"expected 3..8 color-5 cells, got {len(fives)}")
    axis_fives = [
        (row, col)
        for row, col in fives
        if (col if orientation == "top" else row) == axis
    ]
    if axis_fives:
        errors.append(f"color-5 cells may not lie on the selected axis: {axis_fives[:3]}")

    productive = False
    for row, col in fives:
        mirror_row, mirror_col = _mirror(orientation, axis, row, col)
        if 0 <= mirror_row < height and 0 <= mirror_col < width:
            if grid[mirror_row][mirror_col] == 0:
                productive = True
                break
    if not productive:
        errors.append("no color-5 cell has an in-bounds empty reflection target")
    if 0 not in colors:
        errors.append("grid must retain background cells")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height, width = len(grid), len(grid[0])
    orientation, axis = _chosen_axis(grid)
    fives = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    negative = 0
    positive = 0
    any_oob = False
    any_occupied = False
    for row, col in fives:
        coordinate = col if orientation == "top" else row
        if coordinate < axis:
            negative += 1
        elif coordinate > axis:
            positive += 1
        mirror_row, mirror_col = _mirror(orientation, axis, row, col)
        if not (0 <= mirror_row < height and 0 <= mirror_col < width):
            any_oob = True
        elif grid[mirror_row][mirror_col] == 5:
            any_occupied = True
    if negative == positive:
        raise ValueError("shape_side is not observable because side counts tie")
    return {
        "grid_h": height,
        "grid_w": width,
        "orientation": orientation,
        "shape_side": "negative" if negative > positive else "positive",
        "n_5cells": len(fives),
        "edge_case": "out_of_bounds" if any_oob else "occupied" if any_occupied else "clean",
    }


def _source_fives(grid: Grid) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]


def _intended_output(grid: Grid) -> Grid:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height, width = len(grid), len(grid[0])
    orientation, axis = _chosen_axis(grid)
    output = deepcopy(grid)
    for row, col in _source_fives(grid):
        mirror_row, mirror_col = _mirror(orientation, axis, row, col)
        if 0 <= mirror_row < height and 0 <= mirror_col < width:
            if output[mirror_row][mirror_col] == 0:
                output[mirror_row][mirror_col] = 7
    return output


def _overwrite_occupied(grid: Grid) -> Grid:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height, width = len(grid), len(grid[0])
    orientation, axis = _chosen_axis(grid)
    output = deepcopy(grid)
    for row, col in _source_fives(grid):
        mirror_row, mirror_col = _mirror(orientation, axis, row, col)
        if 0 <= mirror_row < height and 0 <= mirror_col < width:
            output[mirror_row][mirror_col] = 7
    return output


def _wrap_out_of_bounds(grid: Grid) -> Grid:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height, width = len(grid), len(grid[0])
    orientation, axis = _chosen_axis(grid)
    output = deepcopy(grid)
    for row, col in _source_fives(grid):
        mirror_row, mirror_col = _mirror(orientation, axis, row, col)
        mirror_row %= height
        mirror_col %= width
        if output[mirror_row][mirror_col] == 0:
            output[mirror_row][mirror_col] = 7
    return output


def _one_side_only(grid: Grid, side: str) -> Grid:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height, width = len(grid), len(grid[0])
    orientation, axis = _chosen_axis(grid)
    output = deepcopy(grid)
    for row, col in _source_fives(grid):
        coordinate = col if orientation == "top" else row
        if side == "negative" and coordinate >= axis:
            continue
        if side == "positive" and coordinate <= axis:
            continue
        mirror_row, mirror_col = _mirror(orientation, axis, row, col)
        if 0 <= mirror_row < height and 0 <= mirror_col < width:
            if output[mirror_row][mirror_col] == 0:
                output[mirror_row][mirror_col] = 7
    return output


def _negative_side_only(grid: Grid) -> Grid:
    return _one_side_only(grid, "negative")


def _positive_side_only(grid: Grid) -> Grid:
    return _one_side_only(grid, "positive")


def _vertical_axis_only(grid: Grid) -> Grid:
    orientation, _axis = _chosen_axis(grid)
    return _intended_output(grid) if orientation == "top" else deepcopy(grid)


def _horizontal_axis_only(grid: Grid) -> Grid:
    orientation, _axis = _chosen_axis(grid)
    return _intended_output(grid) if orientation == "left" else deepcopy(grid)


def _identity(grid: Grid) -> Grid:
    return deepcopy(grid)


def _witness(expected_key: str, expected_value: str) -> Callable[[Grid], bool]:
    def predicate(grid: Grid) -> bool:
        try:
            return observe_overrides(grid)[expected_key] == expected_value
        except (TypeError, ValueError):
            return False
    return predicate


SEMANTIC_WITNESSES = {
    "occupied_target": _witness("edge_case", "occupied"),
    "out_of_bounds_target": _witness("edge_case", "out_of_bounds"),
    "negative_side_source": _witness("shape_side", "negative"),
    "positive_side_source": _witness("shape_side", "positive"),
    "top_axis": _witness("orientation", "top"),
    "left_axis": _witness("orientation", "left"),
}

SEMANTIC_RIVALS = {
    "overwrite_occupied": _overwrite_occupied,
    "wrap_out_of_bounds": _wrap_out_of_bounds,
    "negative_side_only": _negative_side_only,
    "positive_side_only": _positive_side_only,
    "vertical_axis_only": _vertical_axis_only,
    "horizontal_axis_only": _horizontal_axis_only,
}

WITNESS_RIVALS = {
    "occupied_target": ("overwrite_occupied",),
    "out_of_bounds_target": ("wrap_out_of_bounds",),
    "negative_side_source": ("positive_side_only",),
    "positive_side_source": ("negative_side_only",),
    "top_axis": ("horizontal_axis_only",),
    "left_axis": ("vertical_axis_only",),
}

CANONICAL_SHORTCUTS = {
    "overwrite_occupied": _overwrite_occupied,
    "wrap_out_of_bounds": _wrap_out_of_bounds,
}

LESSON_COMPETITORS = {
    **SEMANTIC_RIVALS,
    "identity": _identity,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report any declared competitor that survives demos but changes query."""
    reasons: list[str] = []
    for name, solve in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(solve(pair["input"]) == pair["output"] for pair in demos)
            changes_query = solve(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"competitor {name} fits every demonstration but changes the query")
    return reasons
