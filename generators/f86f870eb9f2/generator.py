"""Generator for S21_M3 — fill the highest-density marker room.

The input is a rectangular grid of rooms separated by complete wall rows and
columns.  Walls use colors 1, 7, and 9; room interiors use 0 and green marker
color 3.  Compare marker *density* (marker count / room area), preserve the
walls, and fill the unique densest room with cyan 8.

The teaching distribution deliberately makes the densest room smaller than a
larger distractor that contains more green markers.  This turns the decisive
"density, not raw count or room size" distinction into an observable property
of ordinary samples rather than an occasional accident.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f86f870eb9f2"
TASK_ID = GENERATOR_ID
VERSION = "3.0.1"
RULE_HASH = "1842ae0643b6"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 0-background grid is divided by complete wall rows and columns into "
    "rectangular rooms. Walls are colors 1/7/9 and each room contains green "
    "(3) markers. Compare marker density (3-count divided by room area), then "
    "preserve all walls and fill the unique densest room completely with cyan "
    "8. Ordinary generated scenes include a larger room with more markers but "
    "lower density, explicitly refuting count-only and largest-room shortcuts."
)

INVARIANTS = [
    "the outer border and every internal separator are complete wall lines",
    "wall colors are drawn from {1,7,9}; room interiors contain only 0 and 3",
    "there are at least two rectangular rooms with unequal areas",
    "every room contains at least one color-3 marker",
    "exactly one room has the strictly highest color-3 density",
    "the target room is not completely marked",
    "ordinary draws contain a larger distractor with more markers but lower density",
]

SCENE_PROFILES = (
    "canonical_square",
    "canonical_wide",
    "canonical_tall",
    "wide_matrix",
    "tall_matrix",
    "large_matrix",
    "wide_matrix_alt",
    "tall_matrix_alt",
    "large_matrix_alt",
)
WALL_STYLES = ("canonical_1", "mixed_1_9", "mixed_1_7_9")
DENSITY_PROFILES = ("clear", "close")

# Fixed geometry makes each profile exactly observable from the returned grid.
# The first three reproduce the three canonical room layouts exactly.
_PROFILE_GEOMETRY: dict[str, tuple[tuple[int, ...], tuple[int, ...]]] = {
    "canonical_square": ((3, 5), (3, 5)),
    "canonical_wide": ((5,), (3, 5, 7)),
    "canonical_tall": ((3, 3, 5), (5,)),
    "wide_matrix": ((3, 5), (3, 5, 7)),
    "tall_matrix": ((3, 5, 7), (3, 5)),
    "large_matrix": ((3, 4, 6), (3, 5, 7)),
    "wide_matrix_alt": ((3, 7), (3, 5, 9)),
    "tall_matrix_alt": ((3, 5, 9), (3, 7)),
    "large_matrix_alt": ((3, 5, 9), (3, 5, 9)),
}
_GEOMETRY_PROFILE = {geometry: name for name, geometry in _PROFILE_GEOMETRY.items()}
SCENE_SCHEDULE = (
    "canonical_square", "wide_matrix", "canonical_wide",
    "tall_matrix_alt", "canonical_tall", "large_matrix",
    "canonical_square", "wide_matrix_alt", "canonical_wide",
    "tall_matrix", "canonical_tall", "large_matrix_alt",
)
WALL_SCHEDULE = (
    "canonical_1", "mixed_1_7_9", "canonical_1",
    "mixed_1_7_9", "canonical_1", "mixed_1_7_9",
    "canonical_1", "mixed_1_9", "canonical_1",
    "mixed_1_9", "canonical_1", "mixed_1_9",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "sample-index schedule spanning canonical and expanded layouts",
        "valid": "|".join(SCENE_PROFILES),
    },
    "wall_style": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "|".join(WALL_STYLES),
    },
    "density_profile": {
        "type": "str",
        "default": "alternating clear and near-boundary rational comparisons",
        "valid": "|".join(DENSITY_PROFILES),
    },
}

DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

_WALLS = {1, 7, 9}
_ALLOWED = {0, 1, 3, 7, 9}
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_BAND_OFFSET = {None: 0, "easy": 0, "medium": 2, "hard": 4}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")


def _scheduled_choice(ctx, label: str, options: Sequence[str], scheduled: str) -> str:
    if ctx.overrides.get(label) is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, (scheduled,)))


def _separator_positions(lengths: Sequence[int]) -> list[int]:
    positions = [0]
    cursor = 0
    for length in lengths:
        cursor += int(length) + 1
        positions.append(cursor)
    return positions


def _room_cells(
    row_separators: Sequence[int], col_separators: Sequence[int]
) -> list[list[tuple[int, int]]]:
    rooms: list[list[tuple[int, int]]] = []
    for row_index in range(len(row_separators) - 1):
        for col_index in range(len(col_separators) - 1):
            rooms.append(
                [
                    (row, col)
                    for row in range(row_separators[row_index] + 1, row_separators[row_index + 1])
                    for col in range(col_separators[col_index] + 1, col_separators[col_index + 1])
                ]
            )
    return rooms


def _choose_density_counts(
    target_area: int, distractor_area: int, density_profile: str
) -> tuple[int, int]:
    """Choose target/distractor counts with count and density rankings reversed."""
    candidates: list[tuple[float, float, int, int]] = []
    for target_count in range(1, target_area):
        target_density = target_count / target_area
        for distractor_count in range(target_count + 1, distractor_area):
            gap = target_density - distractor_count / distractor_area
            if gap <= 0:
                continue
            if density_profile == "clear":
                if 0.55 <= target_density <= 0.80 and gap >= 0.18:
                    candidates.append((abs(target_density - 0.68), -gap, target_count, distractor_count))
            elif density_profile == "close":
                if 0.25 <= target_density <= 0.65 and gap <= 0.10:
                    candidates.append((gap, abs(target_density - 0.45), target_count, distractor_count))
            else:  # validated by the keyed draw, retained as a fail-loud guard
                raise ValueError(f"unknown density profile: {density_profile}")
    if not candidates:
        raise ValueError(
            f"no density/count reversal for areas {target_area} and {distractor_area} "
            f"under profile {density_profile}"
        )
    _primary, _secondary, target_count, distractor_count = min(candidates)
    return target_count, distractor_count


def _wall_style_from_colors(colors: set[int]) -> str | None:
    if colors == {1}:
        return "canonical_1"
    if colors == {1, 9}:
        return "mixed_1_9"
    if colors == {1, 7, 9}:
        return "mixed_1_7_9"
    return None


def _density_profile_from_rooms(rooms: Sequence[dict[str, Any]], target_index: int) -> str:
    target = rooms[target_index]
    other_densities = [
        room["marker_count"] / room["area"]
        for index, room in enumerate(rooms)
        if index != target_index
    ]
    gap = target["marker_count"] / target["area"] - max(other_densities)
    return "close" if gap <= 0.10 + 1e-12 else "clear"


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic room-density lesson input."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    offset = _BAND_OFFSET[difficulty]
    scene_scheduled = SCENE_SCHEDULE[(int(sample_index) + offset) % len(SCENE_SCHEDULE)]
    wall_scheduled = WALL_SCHEDULE[(int(sample_index) + offset) % len(WALL_SCHEDULE)]
    density_scheduled = DENSITY_PROFILES[(int(sample_index) + offset) % len(DENSITY_PROFILES)]
    scene_profile = _scheduled_choice(ctx, "scene_profile", SCENE_PROFILES, scene_scheduled)
    wall_style = _scheduled_choice(ctx, "wall_style", WALL_STYLES, wall_scheduled)
    density_profile = _scheduled_choice(ctx, "density_profile", DENSITY_PROFILES, density_scheduled)

    room_heights, room_widths = _PROFILE_GEOMETRY[scene_profile]
    row_separators = _separator_positions(room_heights)
    col_separators = _separator_positions(room_widths)
    height = row_separators[-1] + 1
    width = col_separators[-1] + 1
    grid = full_grid(height, width, 0)

    # Canonical walls are all 1.  The two extended styles preserve 1 while
    # introducing complete 9 separators and optional 7 wall cells.
    for row in range(height):
        for col in range(width):
            if row in row_separators or col in col_separators:
                grid[row][col] = 1
    internal_lines: list[tuple[str, int]] = [
        *(('row', row) for row in row_separators[1:-1]),
        *(('col', col) for col in col_separators[1:-1]),
    ]
    if wall_style in ("mixed_1_9", "mixed_1_7_9"):
        orientation, position = internal_lines[0]
        if orientation == "row":
            for col in range(width):
                grid[position][col] = 9
        else:
            for row in range(height):
                grid[row][position] = 9
    if wall_style == "mixed_1_7_9":
        wall_rng = ctx.draw_rng("wall_seven_cells")
        candidates = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] in (1, 9)
        ]
        wall_rng.shuffle(candidates)
        for row, col in candidates[: min(3, len(candidates))]:
            grid[row][col] = 7

    rooms = _room_cells(row_separators, col_separators)
    areas = [len(cells) for cells in rooms]
    largest_index = max(range(len(rooms)), key=lambda index: areas[index])
    target_candidates = [index for index in range(len(rooms)) if index != largest_index]
    target_index = ctx.draw_rng("target_index").choice(target_candidates)
    target_count, distractor_count = _choose_density_counts(
        areas[target_index], areas[largest_index], density_profile
    )

    marker_counts = [max(1, area // 10) for area in areas]
    marker_counts[target_index] = target_count
    marker_counts[largest_index] = distractor_count
    target_density = target_count / areas[target_index]
    for index, area in enumerate(areas):
        if index in (target_index, largest_index):
            continue
        # Keep every other room safely below the target density while retaining
        # at least one marker as genuine evidence for the comparison.
        marker_counts[index] = min(marker_counts[index], max(1, int(target_density * area) - 1))

    for index, cells in enumerate(rooms):
        marker_rng = ctx.draw_rng(f"markers:{index}")
        for row, col in marker_rng.sample(cells, marker_counts[index]):
            grid[row][col] = 3

    errors = self_check(grid)
    if errors:
        raise AssertionError("constructed invalid room-density scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = {
        "scene_profile": scene_profile,
        "wall_style": wall_style,
        "density_profile": density_profile,
    }
    if observed != requested:
        raise AssertionError(f"override observation mismatch: requested={requested}, observed={observed}")
    return grid


def analyze_scene(grid) -> dict[str, Any]:
    """Return structural facts and explicit errors for a candidate input grid."""
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or any(not isinstance(row, list) for row in grid):
        return {"errors": ["grid must be a non-empty rectangular list"], "rooms": [], "target_index": None}
    height = len(grid)
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        return {"errors": ["grid rows are ragged or empty"], "rooms": [], "target_index": None}
    values = {value for row in grid for value in row}
    unexpected = sorted(values - _ALLOWED)
    if unexpected:
        errors.append(f"unexpected colors: {unexpected}")

    row_separators = [row for row in range(height) if all(grid[row][col] in _WALLS for col in range(width))]
    col_separators = [col for col in range(width) if all(grid[row][col] in _WALLS for row in range(height))]
    if not row_separators or row_separators[0] != 0 or row_separators[-1] != height - 1:
        errors.append("outer top and bottom borders must be complete wall rows")
    if not col_separators or col_separators[0] != 0 or col_separators[-1] != width - 1:
        errors.append("outer left and right borders must be complete wall columns")
    if any(b - a < 2 for a, b in zip(row_separators, row_separators[1:])):
        errors.append("adjacent horizontal wall lines leave an empty room row")
    if any(b - a < 2 for a, b in zip(col_separators, col_separators[1:])):
        errors.append("adjacent vertical wall lines leave an empty room column")

    separator_rows = set(row_separators)
    separator_cols = set(col_separators)
    for row in range(height):
        for col in range(width):
            if grid[row][col] in _WALLS and row not in separator_rows and col not in separator_cols:
                errors.append(f"stray wall cell inside a room at ({row},{col})")
                break
        if errors and errors[-1].startswith("stray wall"):
            break

    rooms: list[dict[str, Any]] = []
    if len(row_separators) >= 2 and len(col_separators) >= 2:
        for row_index in range(len(row_separators) - 1):
            for col_index in range(len(col_separators) - 1):
                top, bottom = row_separators[row_index] + 1, row_separators[row_index + 1]
                left, right = col_separators[col_index] + 1, col_separators[col_index + 1]
                cells = [(row, col) for row in range(top, bottom) for col in range(left, right)]
                if any(grid[row][col] in _WALLS for row, col in cells):
                    errors.append(f"room ({row_index},{col_index}) contains a wall cell")
                room_values = {grid[row][col] for row, col in cells}
                if not room_values <= {0, 3}:
                    errors.append(
                        f"room ({row_index},{col_index}) contains non-room colors {sorted(room_values - {0,3})}"
                    )
                marker_count = sum(grid[row][col] == 3 for row, col in cells)
                rooms.append(
                    {
                        "row_index": row_index,
                        "col_index": col_index,
                        "bbox": (top, left, bottom - 1, right - 1),
                        "height": bottom - top,
                        "width": right - left,
                        "cells": cells,
                        "area": len(cells),
                        "marker_count": marker_count,
                    }
                )

    if len(rooms) < 2:
        errors.append(f"expected at least two rooms, got {len(rooms)}")
    if rooms and any(room["height"] < 3 or room["width"] < 3 for room in rooms):
        errors.append("every room must be at least 3x3")
    if rooms and len({room["area"] for room in rooms}) < 2:
        errors.append("room areas must not all be equal")
    for index, room in enumerate(rooms):
        if room["marker_count"] == 0:
            errors.append(f"room {index} has no color-3 marker evidence")

    target_index: int | None = None
    if rooms:
        winners = []
        for index, room in enumerate(rooms):
            if all(
                index == other_index
                or room["marker_count"] * other["area"] > other["marker_count"] * room["area"]
                for other_index, other in enumerate(rooms)
            ):
                winners.append(index)
        if len(winners) != 1:
            errors.append(f"highest color-3 density room is not unique (winners={winners})")
        else:
            target_index = winners[0]
            if rooms[target_index]["marker_count"] >= rooms[target_index]["area"]:
                errors.append("target room is completely marked, hiding whole-room fill behavior")

    wall_colors = {grid[row][col] for row in range(height) for col in range(width) if grid[row][col] in _WALLS}
    wall_style = _wall_style_from_colors(wall_colors)
    if wall_style is None:
        errors.append(f"wall palette is not one of the declared styles: {sorted(wall_colors)}")

    room_heights = tuple(b - a - 1 for a, b in zip(row_separators, row_separators[1:]))
    room_widths = tuple(b - a - 1 for a, b in zip(col_separators, col_separators[1:]))
    scene_profile = _GEOMETRY_PROFILE.get((room_heights, room_widths))
    return {
        "errors": sorted(set(errors)),
        "height": height,
        "width": width,
        "row_separators": row_separators,
        "col_separators": col_separators,
        "room_heights": room_heights,
        "room_widths": room_widths,
        "rooms": rooms,
        "target_index": target_index,
        "wall_colors": wall_colors,
        "wall_style": wall_style,
        "scene_profile": scene_profile,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(analyze_scene(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """The teaching grammar preserves the canonical room-density semantics."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, str]:
    facts = analyze_scene(grid)
    if facts["errors"]:
        raise ValueError("cannot observe overrides: " + "; ".join(facts["errors"]))
    if facts["scene_profile"] is None:
        raise ValueError(
            "cannot observe scene_profile from geometry "
            f"{facts['room_heights']} x {facts['room_widths']}"
        )
    target_index = facts["target_index"]
    assert target_index is not None
    return {
        "scene_profile": facts["scene_profile"],
        "wall_style": facts["wall_style"],
        "density_profile": _density_profile_from_rooms(facts["rooms"], target_index),
    }


def _walls_grid(grid) -> list[list[int]]:
    return [[value if value in _WALLS else 0 for value in row] for row in grid]


def _paint_room(grid, room_index: int, color: int = 8) -> list[list[int]]:
    facts = analyze_scene(grid)
    if facts["errors"]:
        raise ValueError("invalid scene: " + "; ".join(facts["errors"]))
    output = _walls_grid(grid)
    for row, col in facts["rooms"][room_index]["cells"]:
        output[row][col] = color
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python audit mirror; the canonical Racket remains output authority."""
    facts = analyze_scene(grid)
    if facts["errors"]:
        raise ValueError("invalid scene: " + "; ".join(facts["errors"]))
    target_index = facts["target_index"]
    assert target_index is not None
    return _paint_room(grid, target_index)


def _rival_most_markers(grid) -> list[list[int]]:
    facts = analyze_scene(grid)
    index = max(range(len(facts["rooms"])), key=lambda i: facts["rooms"][i]["marker_count"])
    return _paint_room(grid, index)


def _rival_largest_room(grid) -> list[list[int]]:
    facts = analyze_scene(grid)
    index = max(range(len(facts["rooms"])), key=lambda i: facts["rooms"][i]["area"])
    return _paint_room(grid, index)


def _rival_first_room(grid) -> list[list[int]]:
    return _paint_room(grid, 0)


def _rival_last_room(grid) -> list[list[int]]:
    facts = analyze_scene(grid)
    return _paint_room(grid, len(facts["rooms"]) - 1)


def _rival_marker_cells_only(grid) -> list[list[int]]:
    facts = analyze_scene(grid)
    target_index = facts["target_index"]
    assert target_index is not None
    output = _walls_grid(grid)
    for row, col in facts["rooms"][target_index]["cells"]:
        if grid[row][col] == 3:
            output[row][col] = 8
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "most_markers": _rival_most_markers,
    "largest_room": _rival_largest_room,
    "first_room": _rival_first_room,
    "last_room": _rival_last_room,
    "marker_cells_only": _rival_marker_cells_only,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _valid_facts(grid) -> dict[str, Any] | None:
    facts = analyze_scene(grid)
    return None if facts["errors"] else facts


def _witness(grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    facts = _valid_facts(grid)
    return False if facts is None else bool(predicate(facts))


def _density_beats_count(facts: dict[str, Any]) -> bool:
    target = facts["target_index"]
    return target != max(range(len(facts["rooms"])), key=lambda i: facts["rooms"][i]["marker_count"])


def _density_beats_area(facts: dict[str, Any]) -> bool:
    target = facts["target_index"]
    return target != max(range(len(facts["rooms"])), key=lambda i: facts["rooms"][i]["area"])


SEMANTIC_WITNESSES = {
    "density_beats_raw_marker_count": lambda grid: _witness(grid, _density_beats_count),
    "density_beats_largest_room": lambda grid: _witness(grid, _density_beats_area),
    "whole_room_fill_not_marker_recolor": lambda grid: _witness(
        grid,
        lambda facts: facts["rooms"][facts["target_index"]]["marker_count"]
        < facts["rooms"][facts["target_index"]]["area"],
    ),
    "target_is_first_room": lambda grid: _witness(grid, lambda facts: facts["target_index"] == 0),
    "target_is_not_first_room": lambda grid: _witness(grid, lambda facts: facts["target_index"] != 0),
    "horizontal_partition": lambda grid: _witness(grid, lambda facts: len(facts["row_separators"]) == 2),
    "vertical_partition": lambda grid: _witness(grid, lambda facts: len(facts["col_separators"]) == 2),
    "matrix_partition": lambda grid: _witness(
        grid, lambda facts: len(facts["row_separators"]) > 2 and len(facts["col_separators"]) > 2
    ),
    "close_density_comparison": lambda grid: _witness(
        grid,
        lambda facts: _density_profile_from_rooms(facts["rooms"], facts["target_index"]) == "close",
    ),
    "clear_density_comparison": lambda grid: _witness(
        grid,
        lambda facts: _density_profile_from_rooms(facts["rooms"], facts["target_index"]) == "clear",
    ),
    "extended_wall_palette": lambda grid: _witness(grid, lambda facts: facts["wall_style"] != "canonical_1"),
}

WITNESS_RIVALS = {
    "density_beats_raw_marker_count": ["most_markers"],
    "density_beats_largest_room": ["largest_room"],
    "whole_room_fill_not_marker_recolor": ["marker_cells_only"],
    "target_is_not_first_room": ["first_room"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible shortcut survives the demos."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    prepared: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output")
            continue
        if self_check(demo["input"]):
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output disagrees with the density rule")
            continue
        prepared.append(demo)
    if reasons:
        return sorted(set(reasons))
    if self_check(query["input"]):
        return ["query input is outside the teaching grammar"]
    query_truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in prepared):
            if competitor(query["input"]) != query_truth:
                reasons.append(
                    f"competing rule {name!r} matches every demo but answers the query differently"
                )
    return sorted(set(reasons))
