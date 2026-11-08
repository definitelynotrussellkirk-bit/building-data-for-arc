"""Generator for 17de34436a9f — rotate a cropped body by a corner cue.

A single maroon marker (9) occupies one grid corner.  Remove it, crop the
remaining one-color connected body to its bounding box, then rotate the crop:
TL=identity, TR=90° clockwise, BR=180°, BL=90° counter-clockwise.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "17de34436a9f"
TASK_ID = "17de34436a9f"
VERSION = "3.0.0"
RULE_HASH = "9f94f78b9fd2"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A single color-9 marker at a grid corner selects the rotation applied to "
    "a separate one-color connected body: top-left=identity, top-right=90° "
    "clockwise, bottom-right=180°, bottom-left=90° counter-clockwise. Remove "
    "the marker, crop the body to its bounding box, and emit the rotated crop."
)

INVARIANTS = [
    "background is 0",
    "exactly one color-9 marker occupies exactly one grid corner",
    "one 4-connected body of 4..7 cells uses one nonzero non-9 color",
    "the body is separated from the marker",
]

DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "9", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "9", "valid": "7..14"},
    "marker_corner": {
        "type": "str",
        "default": "scheduled tl|tr|br|bl",
        "valid": "tl|tr|br|bl",
    },
    "body_size": {"type": "int", "default": "scheduled 4..6", "valid": "4..7"},
    "body_color": {"type": "int", "default": "rng 1..8", "valid": "1..8"},
}

_CORNERS = ("tl", "tr", "br", "bl")
SCHEDULE_PROFILES = _CORNERS
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _normalize(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    frozen = frozenset(cells)
    if not frozen:
        return frozen
    min_row = min(row for row, _ in frozen)
    min_col = min(col for _, col in frozen)
    return frozenset((row - min_row, col - min_col) for row, col in frozen)


def _quarter_turn(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    shape = _normalize(cells)
    height = max(row for row, _ in shape) + 1
    return _normalize((col, height - 1 - row) for row, col in shape)


def _rotation_orbit(cells: Iterable[tuple[int, int]]) -> tuple[frozenset[tuple[int, int]], ...]:
    first = _normalize(cells)
    second = _quarter_turn(first)
    third = _quarter_turn(second)
    fourth = _quarter_turn(third)
    return first, second, third, fourth


def _polyomino_bank(size: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Enumerate compact fixed polyominoes whose four rotations are distinct."""
    shapes: set[frozenset[tuple[int, int]]] = {frozenset({(0, 0)})}
    for _ in range(1, size):
        grown: set[frozenset[tuple[int, int]]] = set()
        for shape in shapes:
            for row, col in shape:
                for d_row, d_col in _NEIGHBORS:
                    candidate = (row + d_row, col + d_col)
                    if candidate not in shape:
                        grown.add(_normalize((*shape, candidate)))
        shapes = grown

    useful = []
    for shape in shapes:
        height = max(row for row, _ in shape) + 1
        width = max(col for _, col in shape) + 1
        if height > 4 or width > 4:
            continue
        if len(set(_rotation_orbit(shape))) != 4:
            continue
        useful.append(tuple(sorted(shape)))
    return tuple(sorted(useful))


_SHAPES_BY_SIZE = {size: _polyomino_bank(size) for size in range(4, 8)}
if any(not bank for bank in _SHAPES_BY_SIZE.values()):  # import-time invariant
    raise RuntimeError("failed to construct asymmetric shape bank")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic corner-teaching role for a sequential lesson."""
    del seed, difficulty
    return _CORNERS[int(sample_index) % len(_CORNERS)]


def _scheduled_body_size(sample_index: int, difficulty: str | None) -> int:
    choices = {
        "easy": (4, 5),
        "medium": (4, 5, 6),
        "hard": (5, 6),
        None: (4, 5, 6),
    }[difficulty]
    return choices[int(sample_index) % len(choices)]


def _corner_position(corner: str, height: int, width: int) -> tuple[int, int]:
    return {
        "tl": (0, 0),
        "tr": (0, width - 1),
        "br": (height - 1, width - 1),
        "bl": (height - 1, 0),
    }[corner]


def _corner_name(position: tuple[int, int], height: int, width: int) -> str:
    reverse = {
        (0, 0): "tl",
        (0, width - 1): "tr",
        (height - 1, width - 1): "br",
        (height - 1, 0): "bl",
    }
    return reverse[position]


def _legal_origins(
    shape: tuple[tuple[int, int], ...],
    height: int,
    width: int,
    marker: tuple[int, int],
) -> list[tuple[int, int]]:
    shape_h = max(row for row, _ in shape) + 1
    shape_w = max(col for _, col in shape) + 1
    origins: list[tuple[int, int]] = []
    marker_row, marker_col = marker
    for row0 in range(height - shape_h + 1):
        for col0 in range(width - shape_w + 1):
            placed = [(row0 + row, col0 + col) for row, col in shape]
            if all(
                max(abs(row - marker_row), abs(col - marker_col)) > 1
                for row, col in placed
            ):
                origins.append((row0, col0))
    return origins


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")

    defaults: dict[str, Any] = {
        "grid_h": 9,
        "grid_w": 9,
        "marker_corner": schedule_profile(seed, sample_index, difficulty),
        "body_size": _scheduled_body_size(sample_index, difficulty),
    }
    defaults.update(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=defaults,
    )

    height = ctx.draw_int("grid_h", 7, 14)
    width = ctx.draw_int("grid_w", 7, 14)
    marker_corner = ctx.draw_choice("marker_corner", _CORNERS)
    body_size = ctx.draw_int("body_size", 4, 7)
    body_color = ctx.draw_int("body_color", 1, 8)
    rng = ctx.draw_rng("layout")

    marker = _corner_position(marker_corner, height, width)
    bank = _SHAPES_BY_SIZE[body_size]
    shape = bank[rng.randrange(len(bank))]
    origins = _legal_origins(shape, height, width, marker)
    if not origins:
        raise ValueError(
            f"body_size={body_size} cannot be placed in {height}x{width} "
            f"away from marker_corner={marker_corner}"
        )
    row0, col0 = origins[rng.randrange(len(origins))]

    grid = full_grid(height, width, 0)
    grid[marker[0]][marker[1]] = 9
    for row, col in shape:
        grid[row0 + row][col0 + col] = body_color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid lesson: " + "; ".join(errors))
    return grid


def _analyse(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a non-empty list of rows"]}
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular and non-empty"]}
    height = len(grid)

    for row in grid:
        for value in row:
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                return {
                    "errors": ["grid cells must be integer ARC colors 0..9"],
                    "height": height,
                    "width": width,
                    "marker_cells": [],
                    "marker_corner": None,
                    "body_positions": set(),
                    "body_size": 0,
                    "body_color": None,
                }

    marker_cells = [
        (row_index, col_index)
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value == 9
    ]
    corners = {
        (0, 0),
        (0, width - 1),
        (height - 1, width - 1),
        (height - 1, 0),
    }
    marker_corner = None
    if len(marker_cells) != 1:
        errors.append(f"expected exactly one color-9 marker, got {len(marker_cells)}")
    elif marker_cells[0] not in corners:
        errors.append("the color-9 marker must occupy a grid corner")
    else:
        marker_corner = _corner_name(marker_cells[0], height, width)

    body = [
        (row_index, col_index, value)
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value not in (0, 9)
    ]
    if not 4 <= len(body) <= 7:
        errors.append(f"body must contain 4..7 cells, got {len(body)}")
    body_colors = {value for _, _, value in body}
    if len(body_colors) != 1:
        errors.append(
            "body must use exactly one nonzero non-9 color, got "
            f"{sorted(body_colors)}"
        )
    body_color = next(iter(body_colors)) if len(body_colors) == 1 else None

    body_positions = {(row, col) for row, col, _ in body}
    if body_positions:
        reached = {next(iter(body_positions))}
        frontier = list(reached)
        while frontier:
            row, col = frontier.pop()
            for d_row, d_col in _NEIGHBORS:
                neighbor = (row + d_row, col + d_col)
                if neighbor in body_positions and neighbor not in reached:
                    reached.add(neighbor)
                    frontier.append(neighbor)
        if reached != body_positions:
            errors.append("body must be 4-connected")

    if len(marker_cells) == 1 and body_positions:
        marker_row, marker_col = marker_cells[0]
        if any(
            max(abs(row - marker_row), abs(col - marker_col)) <= 1
            for row, col in body_positions
        ):
            errors.append("body must be separated from the marker")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "marker_cells": marker_cells,
        "marker_corner": marker_corner,
        "body_positions": body_positions,
        "body_size": len(body),
        "body_color": body_color,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyse(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analyse(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "marker_corner": analysis["marker_corner"],
        "body_size": analysis["body_size"],
        "body_color": analysis["body_color"],
    }


def _turn_matrix_clockwise(matrix: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*matrix[::-1], strict=True)]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror used only for semantic tests and rival probes."""
    analysis = _analyse(grid)
    if analysis["errors"]:
        raise ValueError("invalid task input: " + "; ".join(analysis["errors"]))

    positions = analysis["body_positions"]
    min_row = min(row for row, _ in positions)
    max_row = max(row for row, _ in positions)
    min_col = min(col for _, col in positions)
    max_col = max(col for _, col in positions)
    cropped = [
        [
            grid[row][col] if grid[row][col] != 9 else 0
            for col in range(min_col, max_col + 1)
        ]
        for row in range(min_row, max_row + 1)
    ]
    turns = {"tl": 0, "tr": 1, "br": 2, "bl": 3}[analysis["marker_corner"]]
    for _ in range(turns):
        cropped = _turn_matrix_clockwise(cropped)
    return cropped


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical 9x9, three-color structural profile."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analyse(grid)
    strict_errors: list[str] = []
    if (analysis["height"], analysis["width"]) != (9, 9):
        strict_errors.append("canonical profile requires a 9x9 input")
    if not 4 <= analysis["body_size"] <= 6:
        strict_errors.append("canonical profile requires a 4..6-cell body")
    if len({value for row in grid for value in row}) != 3:
        strict_errors.append("canonical profile requires exactly three colors")
    return strict_errors


def _crop_and_turn(grid: list[list[int]], turns: int, *, include_marker: bool = False) -> list[list[int]]:
    cells = [
        (row_index, col_index)
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value != 0 and (include_marker or value != 9)
    ]
    if not cells:
        return [[0]]
    min_row = min(row for row, _ in cells)
    max_row = max(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    max_col = max(col for _, col in cells)
    cropped = [
        [grid[row][col] for col in range(min_col, max_col + 1)]
        for row in range(min_row, max_row + 1)
    ]
    for _ in range(turns % 4):
        cropped = _turn_matrix_clockwise(cropped)
    return cropped


def _rival_bottom_right_identity(grid: list[list[int]]) -> list[list[int]]:
    """Plausible canonical shortcut: treat BR as identity instead of 180°."""
    analysis = _analyse(grid)
    if analysis["errors"]:
        raise ValueError("invalid task input: " + "; ".join(analysis["errors"]))
    correct_turns = {"tl": 0, "tr": 1, "br": 2, "bl": 3}[
        analysis["marker_corner"]
    ]
    turns = 0 if analysis["marker_corner"] == "br" else correct_turns
    return _crop_and_turn(grid, turns)


CANONICAL_SHORTCUTS = {
    "bottom_right_identity": _rival_bottom_right_identity,
}


def _rival_fixed_identity(grid: list[list[int]]) -> list[list[int]]:
    return _crop_and_turn(grid, 0)


def _rival_fixed_clockwise(grid: list[list[int]]) -> list[list[int]]:
    return _crop_and_turn(grid, 1)


def _rival_fixed_half_turn(grid: list[list[int]]) -> list[list[int]]:
    return _crop_and_turn(grid, 2)


def _rival_fixed_counterclockwise(grid: list[list[int]]) -> list[list[int]]:
    return _crop_and_turn(grid, 3)


def _rival_keep_marker(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analyse(grid)
    if analysis["errors"]:
        raise ValueError("invalid task input: " + "; ".join(analysis["errors"]))
    turns = {"tl": 0, "tr": 1, "br": 2, "bl": 3}[
        analysis["marker_corner"]
    ]
    return _crop_and_turn(grid, turns, include_marker=True)


def _witness_corner(grid: list[list[int]], corner: str) -> bool:
    analysis = _analyse(grid)
    return not analysis["errors"] and analysis["marker_corner"] == corner


def _witness_top_left(grid: list[list[int]]) -> bool:
    return _witness_corner(grid, "tl")


def _witness_top_right(grid: list[list[int]]) -> bool:
    return _witness_corner(grid, "tr")


def _witness_bottom_right(grid: list[list[int]]) -> bool:
    return _witness_corner(grid, "br")


def _witness_bottom_left(grid: list[list[int]]) -> bool:
    return _witness_corner(grid, "bl")


def _witness_marker_removed(grid: list[list[int]]) -> bool:
    return not self_check(grid) and _rival_keep_marker(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "top_left_means_identity": _witness_top_left,
    "top_right_means_clockwise": _witness_top_right,
    "bottom_right_means_half_turn": _witness_bottom_right,
    "bottom_left_means_counterclockwise": _witness_bottom_left,
    "corner_marker_is_removed_before_crop": _witness_marker_removed,
}

SEMANTIC_RIVALS = {
    "fixed_identity": _rival_fixed_identity,
    "fixed_clockwise": _rival_fixed_clockwise,
    "fixed_half_turn": _rival_fixed_half_turn,
    "fixed_counterclockwise": _rival_fixed_counterclockwise,
    "bottom_right_identity": _rival_bottom_right_identity,
    "keep_marker": _rival_keep_marker,
}

WITNESS_RIVALS = {
    "top_left_means_identity": ["fixed_clockwise"],
    "top_right_means_clockwise": ["fixed_identity"],
    "bottom_right_means_half_turn": ["bottom_right_identity"],
    "bottom_left_means_counterclockwise": ["fixed_identity"],
    "corner_marker_is_removed_before_crop": ["keep_marker"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Name every wrong rule that survives all demos but changes the query."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"competitor {name!r} fits every demo but changes the query answer"
                )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Return malformed task-local scenes that the structural checker rejects."""

    def lawful() -> list[list[int]]:
        grid = full_grid(7, 7, 0)
        grid[0][0] = 9
        for row, col in ((3, 3), (4, 3), (5, 3), (5, 4)):
            grid[row][col] = 4
        return grid

    fixtures: list[tuple[str, list[list[int]]]] = []

    missing = lawful()
    missing[0][0] = 0
    fixtures.append(("missing_marker", missing))

    duplicate = lawful()
    duplicate[-1][-1] = 9
    fixtures.append(("duplicate_marker", duplicate))

    displaced = lawful()
    displaced[0][0] = 0
    displaced[0][2] = 9
    fixtures.append(("marker_not_corner", displaced))

    disconnected = full_grid(7, 7, 0)
    disconnected[0][0] = 9
    for row, col in ((3, 2), (4, 2), (5, 2), (2, 5)):
        disconnected[row][col] = 4
    fixtures.append(("disconnected_body", disconnected))

    multicolor = lawful()
    multicolor[5][4] = 6
    fixtures.append(("multicolor_body", multicolor))

    touching = full_grid(7, 7, 0)
    touching[0][0] = 9
    for row, col in ((1, 1), (2, 1), (3, 1), (3, 2)):
        touching[row][col] = 4
    fixtures.append(("body_touches_marker", touching))

    illegal = lawful()
    illegal[3][3] = 10
    fixtures.append(("illegal_color", illegal))

    ragged = lawful()
    ragged[-1].pop()
    fixtures.append(("ragged_grid", ragged))

    return fixtures
