"""Semantic generator for 5271d2407456, "Room Fill by Seeds".

Cyan (8) forms a hollow outer frame and internal walls.  The walls partition
its interior into two, three, or four chambers.  Every chamber contains exactly
one non-cyan colored seed.  The executable rule fills each chamber's connected
zero region with its own seed color while preserving the walls and seeds.

The default distribution retains a keyed prior over the three published
wall profiles while also sampling broader lawful layouts.  Those layouts
include vertical strips, T partitions, offset partial walls on opposite sides
of a full divider, rotations, and a cross.  The broader branch prevents
fixed-orientation and fixed-position shortcuts without statistically erasing
the demonstrated family.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid


GENERATOR_ID = "5271d2407456"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "e38426ae8552"

SUMMARY = (
    "A zero-background grid contains one cyan outer frame and cyan internal "
    "walls that form 2-4 connected chambers. Every chamber has exactly one "
    "distinct non-{0,8} seed; fill all zero cells in that chamber with its "
    "seed color."
)

INVARIANTS = [
    "zero is the only color outside the margin-one cyan frame",
    "the frame interior is partitioned by one declared cyan wall layout",
    "there are two through four chambers and every chamber has at least two cells",
    "every chamber contains exactly one seed and at least one connected zero region",
    "seed colors are distinct and exclude zero and cyan",
    "applying the rule changes every chamber and preserves all walls and seeds",
]

LAYOUTS = (
    "vertical_2",
    "vertical_3",
    "horizontal_2",
    "cross_4",
    "t_left_3",
    "t_right_3",
    "t_top_3",
    "t_bottom_3",
    "staggered_vertical_4",
    "staggered_horizontal_4",
)

ROOMS_BY_LAYOUT = {
    "vertical_2": 2,
    "vertical_3": 3,
    "horizontal_2": 2,
    "cross_4": 4,
    "t_left_3": 3,
    "t_right_3": 3,
    "t_top_3": 3,
    "t_bottom_3": 3,
    "staggered_vertical_4": 4,
    "staggered_horizontal_4": 4,
}

_CANONICAL_PROFILE_RATE = 0.30
_CANONICAL_PROFILES = (
    {
        "name": "train_t_right_3",
        "height": 9,
        "width": 13,
        "layout": "t_right_3",
        "walls": frozenset(
            {(row, 5) for row in range(2, 7)}
            | {(4, column) for column in range(6, 11)}
        ),
    },
    {
        "name": "train_vertical_3",
        "height": 10,
        "width": 14,
        "layout": "vertical_3",
        "walls": frozenset(
            {(row, column) for row in range(2, 8) for column in (4, 8)}
        ),
    },
    {
        "name": "test_staggered_vertical_4",
        "height": 10,
        "width": 14,
        "layout": "staggered_vertical_4",
        "walls": frozenset(
            {(row, 6) for row in range(2, 8)}
            | {(3, column) for column in range(2, 6)}
            | {(5, column) for column in range(7, 12)}
        ),
    },
)

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile prior or difficulty-aware 9..14 draw",
        "valid": "9..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile prior or difficulty-aware 12..16 draw",
        "valid": "12..16",
    },
    "layout": {
        "type": "str",
        "default": "canonical-profile prior or keyed choice across all layouts",
        "valid": "|".join(LAYOUTS),
    },
}

_SEED_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, lower, upper in (("grid_h", 9, 14), ("grid_w", 12, 16)):
        value = overrides.get(name)
        if value is not None and (
            type(value) is not int or not lower <= value <= upper
        ):
            raise ValueError(
                f"{name} must be an integer in [{lower}, {upper}]"
            )
    layout = overrides.get("layout")
    if layout is not None and layout not in LAYOUTS:
        raise ValueError(
            f"layout must be one of {', '.join(LAYOUTS)}"
        )


def _valid_single_splits(start: int, end: int) -> tuple[int, ...]:
    """Wall coordinates leaving at least two passable cells on both sides."""
    return tuple(range(start + 2, end - 1))


def _valid_relaxed_splits(start: int, end: int) -> tuple[int, ...]:
    """Wall coordinates leaving at least one passable cell on both sides."""
    return tuple(range(start + 1, end))


def _valid_double_splits(start: int, end: int) -> tuple[tuple[int, int], ...]:
    """Two wall coordinates leaving at least two cells in all three rooms."""
    return tuple(
        (left, right)
        for left in range(start + 2, end - 1)
        for right in range(left + 3, end - 1)
        if end - right >= 2
    )


def _vertical_wall(rows: range, column: int) -> set[tuple[int, int]]:
    return {(row, column) for row in rows}


def _horizontal_wall(columns: range, row: int) -> set[tuple[int, int]]:
    return {(row, column) for column in columns}


@lru_cache(maxsize=None)
def _wall_candidates(
    height: int, width: int, layout: str
) -> tuple[frozenset[tuple[int, int]], ...]:
    """Enumerate every lawful internal-wall set for one structural layout."""
    rows = range(2, height - 2)
    columns = range(2, width - 2)
    row_splits = _valid_single_splits(2, height - 3)
    col_splits = _valid_single_splits(2, width - 3)
    relaxed_row_splits = _valid_relaxed_splits(2, height - 3)
    relaxed_col_splits = _valid_relaxed_splits(2, width - 3)
    candidates: list[frozenset[tuple[int, int]]] = []

    if layout == "vertical_2":
        candidates.extend(
            frozenset(_vertical_wall(rows, column))
            for column in col_splits
        )
    elif layout == "vertical_3":
        candidates.extend(
            frozenset(
                _vertical_wall(rows, left)
                | _vertical_wall(rows, right)
            )
            for left, right in _valid_double_splits(2, width - 3)
        )
    elif layout == "horizontal_2":
        candidates.extend(
            frozenset(_horizontal_wall(columns, row))
            for row in row_splits
        )
    elif layout == "cross_4":
        candidates.extend(
            frozenset(
                _vertical_wall(rows, column)
                | _horizontal_wall(columns, row)
            )
            for row in row_splits
            for column in col_splits
        )
    elif layout in ("t_left_3", "t_right_3"):
        for row in row_splits:
            for column in col_splits:
                side = (
                    range(2, column)
                    if layout == "t_left_3"
                    else range(column + 1, width - 2)
                )
                candidates.append(
                    frozenset(
                        _vertical_wall(rows, column)
                        | _horizontal_wall(side, row)
                    )
                )
    elif layout in ("t_top_3", "t_bottom_3"):
        for row in row_splits:
            for column in col_splits:
                side = (
                    range(2, row)
                    if layout == "t_top_3"
                    else range(row + 1, height - 2)
                )
                candidates.append(
                    frozenset(
                        _horizontal_wall(columns, row)
                        | _vertical_wall(side, column)
                    )
                )
    elif layout == "staggered_vertical_4":
        for column in col_splits:
            for left_row in relaxed_row_splits:
                for right_row in relaxed_row_splits:
                    if left_row == right_row:
                        continue
                    candidates.append(
                        frozenset(
                            _vertical_wall(rows, column)
                            | _horizontal_wall(range(2, column), left_row)
                            | _horizontal_wall(
                                range(column + 1, width - 2), right_row
                            )
                        )
                    )
    elif layout == "staggered_horizontal_4":
        for row in row_splits:
            for top_column in relaxed_col_splits:
                for bottom_column in relaxed_col_splits:
                    if top_column == bottom_column:
                        continue
                    candidates.append(
                        frozenset(
                            _horizontal_wall(columns, row)
                            | _vertical_wall(range(2, row), top_column)
                            | _vertical_wall(
                                range(row + 1, height - 2), bottom_column
                            )
                        )
                    )
    else:  # pragma: no cover - protected by _validate_call
        raise ValueError(f"unknown layout: {layout}")

    if not candidates:
        raise ValueError(
            f"layout {layout!r} has no construction for {height}x{width}"
        )
    return tuple(dict.fromkeys(candidates))


def _components(cells: Iterable[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    remaining = set(cells)
    components: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        component: list[tuple[int, int]] = []
        while queue:
            row, column = queue.popleft()
            component.append((row, column))
            for dr, dc in _CARDINAL:
                neighbor = (row + dr, column + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        components.append(sorted(component))
    return sorted(components, key=lambda component: component[0])


def _interior_chambers(grid) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    return _components(
        (row, column)
        for row in range(2, height - 2)
        for column in range(2, width - 2)
        if grid[row][column] != 8
    )


def _removal_keeps_connected(
    chamber: list[tuple[int, int]], seed_cell: tuple[int, int]
) -> bool:
    remaining = set(chamber) - {seed_cell}
    return bool(remaining) and len(_components(remaining)) == 1


def _classify_layout(grid) -> str | None:
    height, width = len(grid), len(grid[0])
    actual = frozenset(
        (row, column)
        for row in range(2, height - 2)
        for column in range(2, width - 2)
        if grid[row][column] == 8
    )
    matches = [
        layout
        for layout in LAYOUTS
        if actual in _wall_candidates(height, width, layout)
    ]
    return matches[0] if len(matches) == 1 else None


def _canonical_profile_name(grid) -> str | None:
    height, width = len(grid), len(grid[0])
    actual = frozenset(
        (row, column)
        for row in range(2, height - 2)
        for column in range(2, width - 2)
        if grid[row][column] == 8
    )
    for profile in _CANONICAL_PROFILES:
        if (
            height == profile["height"]
            and width == profile["width"]
            and actual == profile["walls"]
        ):
            return str(profile["name"])
    return None


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list or tuple"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty lists or tuples"]
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid cells must be integer ARC colors 0..9"]
    return []


def _analyze_scene(grid) -> dict:
    errors = _grid_errors(grid)
    result = {"errors": errors, "layout": None}
    if errors:
        return result

    height, width = len(grid), len(grid[0])
    if not 9 <= height <= 14:
        errors.append(f"grid height must be in 9..14, got {height}")
    if not 12 <= width <= 16:
        errors.append(f"grid width must be in 12..16, got {width}")
    if errors:
        return result

    frame = {
        (row, column)
        for row in range(1, height - 1)
        for column in range(1, width - 1)
        if row in (1, height - 2) or column in (1, width - 2)
    }
    if any(grid[row][column] != 8 for row, column in frame):
        errors.append("outer cyan frame is incomplete or recolored")

    outside = {
        (row, column)
        for row in range(height)
        for column in range(width)
        if not (1 <= row <= height - 2 and 1 <= column <= width - 2)
    }
    if any(grid[row][column] != 0 for row, column in outside):
        errors.append("all cells outside the cyan frame must be zero")

    layout = _classify_layout(grid)
    if layout is None:
        errors.append("internal cyan walls do not match one declared layout")
        return result

    chambers = _interior_chambers(grid)
    expected_rooms = ROOMS_BY_LAYOUT[layout]
    if len(chambers) != expected_rooms:
        errors.append(
            f"layout {layout} must form {expected_rooms} chambers, "
            f"found {len(chambers)}"
        )

    chamber_records = []
    all_seeds = []
    for index, chamber in enumerate(chambers):
        seeds = [
            (row, column, grid[row][column])
            for row, column in chamber
            if grid[row][column] not in (0, 8)
        ]
        zeros = [
            (row, column)
            for row, column in chamber
            if grid[row][column] == 0
        ]
        if len(chamber) < 2:
            errors.append(
                f"chamber {index} is too small: {len(chamber)} cells"
            )
        if len(seeds) != 1:
            errors.append(
                f"chamber {index} must contain exactly one seed, "
                f"found {len(seeds)}"
            )
        if not zeros:
            errors.append(f"chamber {index} has no zero cells to fill")
        zero_components = _components(zeros)
        if len(zero_components) != 1:
            errors.append(
                f"chamber {index} zero cells must stay connected after "
                f"placing its seed, found {len(zero_components)} components"
            )
        if len(seeds) == 1 and zero_components:
            seed_color = seeds[0][2]
            boundary_colors = {
                grid[row + dr][column + dc]
                for row, column in zero_components[0]
                for dr, dc in _CARDINAL
                if 0 <= row + dr < height
                and 0 <= column + dc < width
                and grid[row + dr][column + dc] not in (0, 8)
            }
            if boundary_colors != {seed_color}:
                errors.append(
                    f"chamber {index} zero region exposes colors "
                    f"{sorted(boundary_colors)}, expected only {seed_color}"
                )
        all_seeds.extend(seeds)
        chamber_records.append(
            {
                "cells": chamber,
                "seeds": seeds,
                "zeros": zeros,
                "zero_components": zero_components,
            }
        )

    seed_colors = [color for _, _, color in all_seeds]
    if len(set(seed_colors)) != len(seed_colors):
        errors.append("seed colors must be distinct across chambers")
    if any(color not in _SEED_COLORS for color in seed_colors):
        errors.append("seed colors must exclude zero and cyan")

    result.update(
        {
            "height": height,
            "width": width,
            "layout": layout,
            "canonical_profile": _canonical_profile_name(grid),
            "chambers": chamber_records,
            "room_count": len(chambers),
            "seeds": all_seeds,
            "errors": errors,
        }
    )
    return result


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "layout": analysis["layout"],
    }


def rule_mirror(grid) -> list[list[int]]:
    """Testing mirror of the canonical Racket rule; never an output authority."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    zero_regions = _components(
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] == 0
    )
    for region in zero_regions:
        colors = {
            grid[row + dr][column + dc]
            for row, column in region
            for dr, dc in _CARDINAL
            if 0 <= row + dr < height
            and 0 <= column + dc < width
            and grid[row + dr][column + dc] not in (0, 8)
        }
        if len(colors) == 1:
            color = next(iter(colors))
            for row, column in region:
                output[row][column] = color
    return output


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
    profile = None
    if (
        not overrides
        and ctx.draw_rng("canonical_profile_gate").random()
        < _CANONICAL_PROFILE_RATE
    ):
        profile = ctx.draw_rng("canonical_profile_choice").choice(
            _CANONICAL_PROFILES
        )
        height = ctx.draw_int(
            "grid_h", int(profile["height"]), int(profile["height"])
        )
        width = ctx.draw_int(
            "grid_w", int(profile["width"]), int(profile["width"])
        )
        layout = ctx.draw_choice("layout", (str(profile["layout"]),))
    else:
        height = ctx.draw_int_diff("grid_h", 9, 14)
        width = ctx.draw_int_diff("grid_w", 12, 16)
        layout = ctx.draw_choice("layout", LAYOUTS)

    grid = full_grid(height, width, 0)
    draw_frame(grid, 1, 1, height - 2, width - 2, 8)
    wall_set = (
        profile["walls"]
        if profile is not None
        else ctx.draw_rng("wall_positions").choice(
            _wall_candidates(height, width, layout)
        )
    )
    for row, column in wall_set:
        grid[row][column] = 8

    chambers = _interior_chambers(grid)
    if len(chambers) != ROOMS_BY_LAYOUT[layout]:
        raise RuntimeError(
            f"internal construction error: {layout} formed {len(chambers)} rooms"
        )

    seed_colors = ctx.draw_rng("seed_colors").sample(
        list(_SEED_COLORS), len(chambers)
    )
    for index, (chamber, color) in enumerate(zip(chambers, seed_colors)):
        candidates = [
            cell
            for cell in chamber
            if _removal_keeps_connected(chamber, cell)
        ]
        if not candidates:
            raise RuntimeError(
                f"internal construction error: room {index} has no safe seed cell"
            )
        row, column = ctx.draw_rng(f"seed_position_{index}").choice(candidates)
        grid[row][column] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:  # fail closed; never return a malformed training instance
        raise RuntimeError("internal construction error: " + "; ".join(errors))
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    return list(_analyze_scene(grid)["errors"])
