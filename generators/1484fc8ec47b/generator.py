"""Generator for S21_E4 — fill the room with the most green markers.

The input is partitioned by complete wall rows and columns into rectangular
rooms.  Room interiors contain background 0 and green marker cells 3.  Count
markers in every room, preserve all wall cells, clear the non-winning room
interiors, and fill the unique maximum-count room with cyan 8.

Ordinary lessons include count-vs-density and count-vs-size controls whenever
the selected geometry permits them.  This prevents a densest-room, largest-room,
fixed-position, or marker-recolor shortcut from explaining a materialized
lesson.  Three named profiles reproduce every canonical input geometry exactly.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1484fc8ec47b"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "33d8fa4b8fcd"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 0-background grid is divided by complete wall rows and columns into "
    "rectangular rooms. Walls use colors 1/7/9 and room interiors use only 0 "
    "and green marker color 3. Count the green markers in each room, preserve "
    "the walls, clear every room interior, and fill the unique maximum-count "
    "room completely with cyan 8. The generated curriculum reproduces all "
    "canonical layouts and regularly makes a smaller room denser while a "
    "different room has the larger raw count, refuting density and size shortcuts."
)

INVARIANTS = [
    "outer borders and internal separators are complete wall rows or columns",
    "wall colors are drawn from {1,7,9}; room interiors contain only 0 and 3",
    "there are at least two rectangular rooms, each at least 3x3",
    "exactly one room has the strictly greatest number of color-3 markers",
    "the winning room is not completely marked, so whole-room fill is visible",
    "at least one losing room contains a marker, so a comparison is required",
]

SCENE_PROFILES = (
    "canonical_matrix_2x3",
    "canonical_row_1x3",
    "canonical_matrix_2x2",
    "control_matrix_2x3",
    "control_tall_3x2",
    "control_wide_2x4",
)
WALL_STYLES = ("canonical_1", "mixed_1_9", "mixed_1_7_9")
COUNT_PROFILES = ("close", "clear")

# The first three layouts exactly match the canonical row/column separator
# geometry.  Control layouts have at least three room areas so the raw-count
# winner can be neither the densest nor the largest room.
_PROFILE_GEOMETRY: dict[str, tuple[tuple[int, ...], tuple[int, ...]]] = {
    "canonical_matrix_2x3": ((3, 3), (3, 4, 3)),
    "canonical_row_1x3": ((5,), (3, 5, 3)),
    "canonical_matrix_2x2": ((3, 5), (5, 3)),
    "control_matrix_2x3": ((3, 5), (3, 5, 7)),
    "control_tall_3x2": ((3, 5, 7), (3, 5)),
    "control_wide_2x4": ((3, 6), (3, 4, 6, 8)),
}
_GEOMETRY_PROFILE = {geometry: name for name, geometry in _PROFILE_GEOMETRY.items()}

# Every three consecutive samples include at least two geometries that support
# both count-vs-density and count-vs-largest controls.  The one unavoidable
# exception is canonical_row_1x3: its middle room is uniquely largest, exactly
# as in the official example.  The surrounding control slots kill that rival
# at the lesson level.
_SCENE_SCHEDULE = (
    "canonical_row_1x3",
    "canonical_matrix_2x3",
    "canonical_matrix_2x2",
    "canonical_row_1x3",
    "control_matrix_2x3",
    "control_tall_3x2",
    "canonical_row_1x3",
    "control_wide_2x4",
    "canonical_matrix_2x3",
)
_WALL_SCHEDULE = (
    "canonical_1",
    "mixed_1_9",
    "mixed_1_7_9",
    "canonical_1",
    "mixed_1_7_9",
    "canonical_1",
    "mixed_1_9",
    "mixed_1_7_9",
    "canonical_1",
)
_COUNT_SCHEDULE = ("close", "clear", "close", "clear", "close", "clear", "close", "clear", "close")

SCHEDULE_PROFILES = tuple(range(len(_SCENE_SCHEDULE)))

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "sample-index schedule spanning all canonical and control layouts",
        "valid": "|".join(SCENE_PROFILES),
    },
    "wall_style": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "|".join(WALL_STYLES),
    },
    "count_profile": {
        "type": "str",
        "default": "sample-index schedule; close means winner-second gap 1, clear means gap 2",
        "valid": "|".join(COUNT_PROFILES),
    },
}

DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

_WALLS = {1, 7, 9}
_ALLOWED = {0, 1, 3, 7, 9}
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_BAND_OFFSET = {None: 0, "easy": 0, "medium": 3, "hard": 6}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Expose the deterministic nine-slot lesson schedule."""
    del seed
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    return (int(sample_index) + _BAND_OFFSET[difficulty]) % len(SCHEDULE_PROFILES)


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


def _wall_style_from_colors(colors: set[int]) -> str | None:
    if colors == {1}:
        return "canonical_1"
    if colors == {1, 9}:
        return "mixed_1_9"
    if colors == {1, 7, 9}:
        return "mixed_1_7_9"
    return None


def _count_profile_from_rooms(rooms: Sequence[dict[str, Any]], target_index: int) -> str:
    counts = sorted((room["marker_count"] for room in rooms), reverse=True)
    gap = counts[0] - counts[1]
    if gap == 1:
        return "close"
    if gap == 2:
        return "clear"
    raise ValueError(f"winner/runner-up marker gap {gap} is outside declared profiles")


def _first_largest_index(areas: Sequence[int]) -> int:
    return max(range(len(areas)), key=lambda index: areas[index])


def _control_pairs(areas: Sequence[int]) -> list[tuple[int, int]]:
    """Candidate (target, density-rival) pairs for both shortcut controls."""
    first_largest = _first_largest_index(areas)
    return [
        (target, distractor)
        for target, target_area in enumerate(areas)
        for distractor, distractor_area in enumerate(areas)
        if target not in (0, len(areas) - 1)
        and target != first_largest
        and distractor != target
        and target_area > distractor_area
    ]


def _choose_target_pair(areas: Sequence[int], rng) -> tuple[int, int, bool]:
    candidates = _control_pairs(areas)
    if candidates:
        target, distractor = rng.choice(candidates)
        return target, distractor, True

    # The canonical 1x3 profile has one unique largest middle room.  It cannot
    # independently refute a largest-room or density shortcut, so choose the
    # middle room and rely on the surrounding scheduled control examples.
    interior = list(range(1, len(areas) - 1))
    target = max(interior, key=lambda index: areas[index])
    distractor = max((index for index in range(len(areas)) if index != target), key=lambda index: areas[index])
    return target, distractor, False


def _choose_marker_counts(
    target_area: int,
    distractor_area: int,
    count_profile: str,
    require_density_reversal: bool,
) -> tuple[int, int]:
    gap = 1 if count_profile == "close" else 2
    candidates: list[tuple[float, int, int]] = []
    for distractor_count in range(1, distractor_area):
        target_count = distractor_count + gap
        if target_count >= target_area:
            continue
        if require_density_reversal:
            if distractor_count * target_area <= target_count * distractor_area:
                continue
            density_gap = distractor_count / distractor_area - target_count / target_area
            candidates.append((abs(density_gap - 0.12), target_count, distractor_count))
        else:
            candidates.append((abs(target_count / target_area - 0.35), target_count, distractor_count))
    if not candidates:
        raise ValueError(
            f"cannot realize count profile {count_profile} for areas "
            f"target={target_area}, distractor={distractor_area}, "
            f"density_reversal={require_density_reversal}"
        )
    _score, target_count, distractor_count = min(candidates)
    return target_count, distractor_count


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic room-count lesson input."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = schedule_profile(seed, sample_index, difficulty)
    scene_profile = _scheduled_choice(ctx, "scene_profile", SCENE_PROFILES, _SCENE_SCHEDULE[slot])
    wall_style = _scheduled_choice(ctx, "wall_style", WALL_STYLES, _WALL_SCHEDULE[slot])
    count_profile = _scheduled_choice(ctx, "count_profile", COUNT_PROFILES, _COUNT_SCHEDULE[slot])

    room_heights, room_widths = _PROFILE_GEOMETRY[scene_profile]
    row_separators = _separator_positions(room_heights)
    col_separators = _separator_positions(room_widths)
    height = row_separators[-1] + 1
    width = col_separators[-1] + 1
    grid = full_grid(height, width, 0)

    for row in range(height):
        for col in range(width):
            if row in row_separators or col in col_separators:
                grid[row][col] = 1

    internal_lines: list[tuple[str, int]] = [
        *(("row", row) for row in row_separators[1:-1]),
        *(("col", col) for col in col_separators[1:-1]),
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
        candidates = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == 1
        ]
        wall_rng = ctx.draw_rng("wall_seven_cells")
        wall_rng.shuffle(candidates)
        for row, col in candidates[: min(3, len(candidates))]:
            grid[row][col] = 7

    rooms = _room_cells(row_separators, col_separators)
    areas = [len(cells) for cells in rooms]
    target_index, distractor_index, has_both_controls = _choose_target_pair(
        areas, ctx.draw_rng("target_pair")
    )
    target_count, distractor_count = _choose_marker_counts(
        areas[target_index],
        areas[distractor_index],
        count_profile,
        has_both_controls,
    )

    marker_counts = [0 for _ in rooms]
    marker_counts[target_index] = target_count
    marker_counts[distractor_index] = distractor_count
    other_rng = ctx.draw_rng("other_counts")
    for index, area in enumerate(areas):
        if index in (target_index, distractor_index):
            continue
        # Preserve the exact winner/runner-up gap while varying losing evidence.
        marker_counts[index] = other_rng.randint(0, min(distractor_count, area - 1))

    for index, cells in enumerate(rooms):
        marker_rng = ctx.draw_rng(f"markers:{index}")
        for row, col in marker_rng.sample(cells, marker_counts[index]):
            grid[row][col] = 3

    errors = self_check(grid)
    if errors:
        raise AssertionError("constructed invalid room-count scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = {
        "scene_profile": scene_profile,
        "wall_style": wall_style,
        "count_profile": count_profile,
    }
    if observed != requested:
        raise AssertionError(f"override observation mismatch: requested={requested}, observed={observed}")
    return grid


def analyze_scene(grid) -> dict[str, Any]:
    """Return structural room facts and explicit errors for a candidate grid."""
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or any(not isinstance(row, list) for row in grid):
        return {"errors": ["grid must be a non-empty rectangular list"], "rooms": [], "target_index": None}
    height = len(grid)
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        return {"errors": ["grid rows are ragged or empty"], "rooms": [], "target_index": None}
    if height > 30 or width > 30:
        errors.append(f"grid exceeds 30x30: {height}x{width}")

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
    if any(b - a < 4 for a, b in zip(row_separators, row_separators[1:])):
        errors.append("each room row must be at least 3 cells high")
    if any(b - a < 4 for a, b in zip(col_separators, col_separators[1:])):
        errors.append("each room column must be at least 3 cells wide")

    separator_rows = set(row_separators)
    separator_cols = set(col_separators)
    stray_wall = None
    for row in range(height):
        for col in range(width):
            if grid[row][col] in _WALLS and row not in separator_rows and col not in separator_cols:
                stray_wall = (row, col)
                break
        if stray_wall is not None:
            break
    if stray_wall is not None:
        errors.append(f"stray or broken wall cell at {stray_wall}")

    rooms: list[dict[str, Any]] = []
    if len(row_separators) >= 2 and len(col_separators) >= 2:
        for row_index in range(len(row_separators) - 1):
            for col_index in range(len(col_separators) - 1):
                top, bottom = row_separators[row_index] + 1, row_separators[row_index + 1]
                left, right = col_separators[col_index] + 1, col_separators[col_index + 1]
                cells = [(row, col) for row in range(top, bottom) for col in range(left, right)]
                room_values = {grid[row][col] for row, col in cells}
                if not room_values <= {0, 3}:
                    errors.append(
                        f"room ({row_index},{col_index}) contains non-room colors "
                        f"{sorted(room_values - {0, 3})}"
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

    target_index: int | None = None
    if rooms:
        max_count = max(room["marker_count"] for room in rooms)
        winners = [index for index, room in enumerate(rooms) if room["marker_count"] == max_count]
        if len(winners) != 1:
            errors.append(f"maximum color-3 marker count is not unique (winners={winners})")
        else:
            target_index = winners[0]
            target = rooms[target_index]
            if target["marker_count"] < 2:
                errors.append("winning room must contain at least two markers")
            if target["marker_count"] >= target["area"]:
                errors.append("winning room is completely marked, hiding whole-room fill")
            if not any(
                index != target_index and room["marker_count"] > 0
                for index, room in enumerate(rooms)
            ):
                errors.append("no losing room contains marker evidence")

    wall_colors = {
        grid[row][col]
        for row in range(height)
        for col in range(width)
        if grid[row][col] in _WALLS
    }
    wall_style = _wall_style_from_colors(wall_colors)
    if wall_style is None:
        errors.append(f"wall palette is not a declared style: {sorted(wall_colors)}")

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
    """The teaching grammar is the canonical complete-wall room grammar."""
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
        "count_profile": _count_profile_from_rooms(facts["rooms"], target_index),
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
    """Pure Python audit mirror; canonical Racket remains output authority."""
    facts = analyze_scene(grid)
    if facts["errors"]:
        raise ValueError("invalid scene: " + "; ".join(facts["errors"]))
    target_index = facts["target_index"]
    assert target_index is not None
    return _paint_room(grid, target_index)


def _rival_densest_room(grid) -> list[list[int]]:
    facts = analyze_scene(grid)
    index = max(
        range(len(facts["rooms"])),
        key=lambda i: facts["rooms"][i]["marker_count"] / facts["rooms"][i]["area"],
    )
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
    "densest_room": _rival_densest_room,
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


def _count_beats_density(facts: dict[str, Any]) -> bool:
    target = facts["target_index"]
    densest = max(
        range(len(facts["rooms"])),
        key=lambda i: facts["rooms"][i]["marker_count"] / facts["rooms"][i]["area"],
    )
    return target != densest


def _count_beats_area(facts: dict[str, Any]) -> bool:
    target = facts["target_index"]
    largest = max(range(len(facts["rooms"])), key=lambda i: facts["rooms"][i]["area"])
    return target != largest


SEMANTIC_WITNESSES = {
    "raw_count_beats_density": lambda grid: _witness(grid, _count_beats_density),
    "raw_count_beats_largest_room": lambda grid: _witness(grid, _count_beats_area),
    "whole_room_fill_not_marker_recolor": lambda grid: _witness(
        grid,
        lambda facts: facts["rooms"][facts["target_index"]]["marker_count"]
        < facts["rooms"][facts["target_index"]]["area"],
    ),
    "target_is_not_first_room": lambda grid: _witness(grid, lambda facts: facts["target_index"] != 0),
    "target_is_not_last_room": lambda grid: _witness(
        grid, lambda facts: facts["target_index"] != len(facts["rooms"]) - 1
    ),
}

WITNESS_RIVALS = {
    "raw_count_beats_density": ["densest_room"],
    "raw_count_beats_largest_room": ["largest_room"],
    "whole_room_fill_not_marker_recolor": ["marker_cells_only"],
    "target_is_not_first_room": ["first_room"],
    "target_is_not_last_room": ["last_room"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible shortcut survives all demos."""
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
            reasons.append(f"demo {index} output disagrees with the maximum-count rule")
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
