"""Generator for ``Sequential Arrow Slides`` (task ea957ff0d072).

Colors 1/2/3/4 are direction markers for left/right/up/down.  All marker
cells are removed first.  Markers are then processed in row-major order; the
same-color component touching a marker is translated repeatedly in the
marker color's direction until the next step would leave the grid or collide
with the current nonzero state.  Color 8 is a fixed vertical wall/obstacle.

The public examples make two shortcuts especially tempting: treating the
marker *position* as the direction (the marker is always behind its object),
and treating the wall as the destination.  The four-slot schedule retains
canonical-scale anchors while adding explicit counterexamples to both and a
constructive earlier-move-blocks-later case for the row-major update rule.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ea957ff0d072"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "d849dec31c02"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A black grid contains one full-height color-8 wall and 2-3 distinct "
    "colored polyominoes, each touching one direction marker: 1=left, "
    "2=right, 3=up, 4=down. Remove every marker, then process their original "
    "positions in row-major order. At each marker, slide the currently "
    "adjacent same-color component repeatedly in the marker direction until "
    "blocked by the current grid, so an earlier move can block a later one."
)

INVARIANTS = [
    "background is 0 and exactly one full-height color-8 wall is present",
    "there are 2-3 distinct 3-4 cell 4-connected objects in colors {5,6,7,9}",
    "each object is selected by exactly one adjacent marker in {1,2,3,4}",
    "all marker cells are cleared before row-major sequential slides begin",
    "at least two marker directions are shown and the selected rule changes the grid",
]

_DIRECTIONS: dict[int, tuple[int, int]] = {
    1: (0, -1),
    2: (0, 1),
    3: (-1, 0),
    4: (1, 0),
}
_CARDINAL = tuple(_DIRECTIONS.values())
_BLOB_COLORS = (5, 6, 7, 9)

SCHEDULE_PROFILES = (
    "canonical_independent",
    "canonical_order_block",
    "canonical_three_way",
    "attachment_counterexample",
)

_SCHEDULE = (
    {
        "profile": "canonical_independent",
        "grid_h": 8,
        "grid_w": 12,
        "n_objects": 2,
        "wall_position": "interior",
        "marker_attachment": "trailing",
    },
    {
        "profile": "canonical_order_block",
        "grid_h": 9,
        "grid_w": 12,
        "n_objects": 2,
        "wall_position": "edge",
        "marker_attachment": "trailing",
    },
    {
        "profile": "canonical_three_way",
        "grid_h": 9,
        "grid_w": 13,
        "n_objects": 3,
        "wall_position": "interior",
        "marker_attachment": "trailing",
    },
    {
        "profile": "attachment_counterexample",
        "grid_h": None,
        "grid_w": None,
        "n_objects": None,
        "wall_position": None,
        "marker_attachment": "mixed",
    },
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchors in slots 0..2; difficulty draw in slot 3",
        "valid": "8..16",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchors in slots 0..2; difficulty draw in slot 3",
        "valid": "12..20",
    },
    "n_objects": {
        "type": "int",
        "default": "2,2,3 schedule then rng",
        "valid": "2..3",
    },
    "wall_position": {
        "type": "str",
        "default": "canonical schedule then rng",
        "valid": "edge|interior",
    },
    "marker_attachment": {
        "type": "str",
        "default": "trailing in canonical anchors; mixed in shortcut counterexample",
        "valid": "trailing|mixed",
    },
}

# Every boundary combination above is constructible; opt into strict override
# rejection accounting rather than the legacy warning-only policy.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    for name in ("grid_h", "grid_w", "n_objects"):
        value = overrides.get(name)
        if value is not None and (type(value) is not int):
            raise ValueError(f"{name} must be an integer")
    for name in ("wall_position", "marker_attachment"):
        value = overrides.get(name)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{name} must be a string")


def _scheduled_int(
    ctx,
    label: str,
    scheduled: int | None,
    lo: int,
    hi: int,
    overrides: dict[str, Any],
    *,
    difficulty_draw: bool = False,
) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    if scheduled is not None:
        return ctx.draw_int(label, scheduled, scheduled)
    if difficulty_draw:
        return ctx.draw_int_diff(label, lo, hi)
    return ctx.draw_int(label, lo, hi)


def _scheduled_choice(
    ctx,
    label: str,
    scheduled: str | None,
    options: tuple[str, ...],
    overrides: dict[str, Any],
) -> str:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    if scheduled is not None:
        return ctx.draw_choice(label, (scheduled,))
    return ctx.draw_choice(label, options)


def _paint_wall(grid: list[list[int]], wall_col: int) -> None:
    for row in grid:
        row[wall_col] = 8


def _paint(
    grid: list[list[int]],
    cells: list[tuple[int, int]],
    color: int,
) -> None:
    h, w = len(grid), len(grid[0])
    for r, c in cells:
        if not (0 <= r < h and 0 <= c < w):
            raise ValueError(f"scene construction placed {color} out of bounds at {(r, c)}")
        if grid[r][c] != 0:
            raise ValueError(
                f"scene construction collision at {(r, c)}: {grid[r][c]} then {color}"
            )
    for r, c in cells:
        grid[r][c] = color


def _paint_marker(
    grid: list[list[int]], position: tuple[int, int], marker: int
) -> None:
    _paint(grid, [position], marker)


_HORIZONTAL_MARKER = {1: 2, 2: 1, 3: 3, 4: 4}
_VERTICAL_MARKER = {1: 1, 2: 2, 3: 4, 4: 3}


def _reflect_horizontal(grid: list[list[int]]) -> list[list[int]]:
    """Reflect left/right while preserving marker-direction semantics."""
    return [
        [_HORIZONTAL_MARKER.get(value, value) for value in reversed(row)]
        for row in grid
    ]


def _reflect_vertical(grid: list[list[int]]) -> list[list[int]]:
    """Reflect top/bottom while preserving marker-direction semantics."""
    return [
        [_VERTICAL_MARKER.get(value, value) for value in row]
        for row in reversed(grid)
    ]


def _wall_column(profile: str, mode: str, w: int, rng) -> int:
    if mode == "edge":
        return 0
    if profile == "canonical_independent":
        return w - 2
    if profile == "canonical_order_block":
        return min(2, w - 6)
    if profile == "canonical_three_way":
        return w // 2
    return rng.randint(2, max(2, w - 7))


def _scene_independent(
    grid: list[list[int]],
    wall_col: int,
    colors: list[int],
    n_objects: int,
    attachment: str,
) -> None:
    h, w = len(grid), len(grid[0])
    mixed = attachment == "mixed"

    if wall_col == 0:
        a_left = 4
        a_cells = [(1, a_left + offset) for offset in range(3)]
        a_marker = (1, a_left - 1) if mixed else (0, a_left)
        b_cells = [(2, w - 3), (2, w - 2), (3, w - 3)]
        b_marker = (2, w - 1)
        b_direction = 1
        c_col = 3
        c_direction = 2
        c_marker_col = c_col - 1
    else:
        a_left = max(4, wall_col - 4)
        a_cells = [(1, a_left + offset) for offset in range(3)]
        a_marker = (1, a_left - 1) if mixed else (0, a_left)
        b_cells = [(2, 1), (2, 2), (3, 2)]
        b_marker = (2, 0)
        b_direction = 2
        c_col = max(4, wall_col - 3)
        c_direction = 1
        c_marker_col = c_col + 1

    _paint(grid, a_cells, colors[0])
    _paint_marker(grid, a_marker, 4)
    _paint(grid, b_cells, colors[1])
    _paint_marker(grid, b_marker, b_direction)

    if n_objects == 3:
        c_rows = [h - 4, h - 3, h - 2]
        c_cells = [(row, c_col) for row in c_rows]
        _paint(grid, c_cells, colors[2])
        _paint_marker(grid, (h - 3, c_marker_col), c_direction)


def _scene_order_block(
    grid: list[list[int]],
    wall_col: int,
    colors: list[int],
    n_objects: int,
    attachment: str,
) -> None:
    h, w = len(grid), len(grid[0])
    a_top = h - 6
    a_cells = [
        (a_top, w - 3),
        (a_top, w - 2),
        (a_top + 1, w - 3),
        (a_top + 1, w - 2),
    ]
    a_marker = (
        (a_top - 1, w - 3)
        if attachment == "mixed"
        else (a_top, w - 1)
    )

    b_col = wall_col + 2
    b_top = h - 4
    b_cells = [
        (b_top, b_col),
        (b_top + 1, b_col),
        (b_top + 2, b_col),
        (b_top + 2, b_col + 1),
    ]
    b_marker = (h - 1, b_col)

    if n_objects == 3:
        c_start = wall_col + 4
        c_cells = [(0, c_start + offset) for offset in range(3)]
        _paint(grid, c_cells, colors[2])
        _paint_marker(grid, (0, c_start - 1), 2)

    _paint(grid, a_cells, colors[0])
    _paint_marker(grid, a_marker, 1)
    _paint(grid, b_cells, colors[1])
    _paint_marker(grid, b_marker, 3)


def _scene_three_way(
    grid: list[list[int]],
    wall_col: int,
    colors: list[int],
    n_objects: int,
    attachment: str,
) -> None:
    h, w = len(grid), len(grid[0])
    a_left = max(5, w // 2 - 1) if wall_col == 0 else wall_col + 2
    a_cells = [
        (1, a_left),
        (1, a_left + 1),
        (2, a_left),
        (2, a_left + 1),
    ]
    a_marker = (
        (1, a_left - 1) if attachment == "mixed" else (0, a_left)
    )

    c_col = w - 2
    c_cells = [(h - 4, c_col), (h - 3, c_col), (h - 2, c_col)]
    c_marker = (h - 3, w - 1)

    _paint(grid, a_cells, colors[0])
    _paint_marker(grid, a_marker, 4)

    if n_objects == 3:
        if wall_col == 0:
            b_cells = [(2, 2), (2, 3), (3, 3), (3, 4)]
            b_marker = (2, 1)
        else:
            b_cells = [(2, 1), (2, 2), (3, 2), (3, 3)]
            b_marker = (2, 0)
        _paint(grid, b_cells, colors[1])
        _paint_marker(grid, b_marker, 2)
        c_color = colors[2]
    else:
        c_color = colors[1]

    _paint(grid, c_cells, c_color)
    _paint_marker(grid, c_marker, 1)


def _scene_attachment_counterexample(
    grid: list[list[int]],
    wall_col: int,
    colors: list[int],
    n_objects: int,
    attachment: str,
) -> None:
    h, w = len(grid), len(grid[0])
    left = wall_col + 2

    # The color-3 marker is deliberately beside (not below) the payload in the
    # mixed branch, so "move away from the marker" predicts right while the
    # actual color key predicts up.
    a_cells = [(h - 2, left + offset) for offset in range(3)]
    a_marker = (
        (h - 2, left - 1)
        if attachment == "mixed"
        else (h - 1, left)
    )

    b_cells = [(1, left + offset) for offset in range(3)]
    b_marker = (1, left - 1)

    _paint(grid, b_cells, colors[0])
    _paint_marker(grid, b_marker, 2)
    _paint(grid, a_cells, colors[1])
    _paint_marker(grid, a_marker, 3)

    if n_objects == 3:
        # Keep the optional third object in the top band.  Its leftward move
        # must never make it adjacent to the later mixed-attachment marker,
        # otherwise row-major dynamic selection can steal that marker and hide
        # the intended color-vs-position counterexample.
        c_cells = [(1, w - 2), (2, w - 2), (3, w - 2)]
        _paint(grid, c_cells, colors[2])
        _paint_marker(grid, (2, w - 1), 1)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one lawful input; every declared override is exact or loud."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = _SCHEDULE[int(sample_index) % len(_SCHEDULE)]
    profile = slot["profile"]

    h = _scheduled_int(
        ctx,
        "grid_h",
        slot["grid_h"],
        8,
        16,
        overrides,
        difficulty_draw=slot["grid_h"] is None,
    )
    w = _scheduled_int(
        ctx,
        "grid_w",
        slot["grid_w"],
        12,
        20,
        overrides,
        difficulty_draw=slot["grid_w"] is None,
    )
    n_objects = _scheduled_int(
        ctx, "n_objects", slot["n_objects"], 2, 3, overrides
    )
    wall_position = _scheduled_choice(
        ctx,
        "wall_position",
        slot["wall_position"],
        ("edge", "interior"),
        overrides,
    )
    marker_attachment = _scheduled_choice(
        ctx,
        "marker_attachment",
        slot["marker_attachment"],
        ("trailing", "mixed"),
        overrides,
    )

    rng = ctx.draw_rng(f"layout:{profile}:{difficulty or 'unbanded'}")
    wall_col = _wall_column(profile, wall_position, w, rng)
    colors = list(rng.sample(_BLOB_COLORS, n_objects))
    grid = full_grid(h, w, 0)
    _paint_wall(grid, wall_col)

    builders = {
        "canonical_independent": _scene_independent,
        "canonical_order_block": _scene_order_block,
        "canonical_three_way": _scene_three_way,
        "attachment_counterexample": _scene_attachment_counterexample,
    }
    builders[profile](grid, wall_col, colors, n_objects, marker_attachment)
    if rng.choice((False, True)):
        grid = _reflect_horizontal(grid)
    # Couple the two vertical-orientation choices through the lesson seed.
    # Every four consecutive schedule slots therefore keep one down-marker
    # anchor while both profiles still vary across lessons.
    vertical_phase = bool((int(seed) ^ (int(seed) >> 17)) & 1)
    if (profile == "canonical_independent" and vertical_phase) or (
        profile == "canonical_three_way" and not vertical_phase
    ):
        grid = _reflect_vertical(grid)

    problems = self_check(grid)
    if problems:
        raise AssertionError(
            f"internal {profile} construction violated its contract: {problems}"
        )
    return grid


def _rectangular_grid(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, list) or not grid:
        return 0, 0, ["grid must be a nonempty list"]
    if not all(isinstance(row, list) and row for row in grid):
        return 0, 0, ["grid rows must be nonempty lists"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return len(grid), w, ["grid must be rectangular"]
    if any(type(value) is not int for row in grid for value in row):
        return len(grid), w, ["grid cells must be integers"]
    return len(grid), w, []


def _component(
    grid: list[list[int]], start: tuple[int, int]
) -> list[tuple[int, int]]:
    h, w = len(grid), len(grid[0])
    color = grid[start[0]][start[1]]
    seen = {start}
    stack = [start]
    cells: list[tuple[int, int]] = []
    while stack:
        r, c = stack.pop()
        cells.append((r, c))
        for dr, dc in _CARDINAL:
            nr, nc = r + dr, c + dc
            nxt = (nr, nc)
            if (
                0 <= nr < h
                and 0 <= nc < w
                and nxt not in seen
                and grid[nr][nc] == color
            ):
                seen.add(nxt)
                stack.append(nxt)
    return sorted(cells)


def _all_components(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] not in _BLOB_COLORS or (r, c) in seen:
                continue
            cells = _component(grid, (r, c))
            seen.update(cells)
            result.append({"color": grid[r][c], "cells": cells})
    return result


def _initial_analysis(grid: Any) -> dict[str, Any]:
    h, w, errors = _rectangular_grid(grid)
    result: dict[str, Any] = {
        "h": h,
        "w": w,
        "errors": list(errors),
        "wall_col": None,
        "markers": [],
        "components": [],
        "associations": [],
    }
    if errors:
        return result

    allowed = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}
    unexpected = sorted({value for row in grid for value in row} - allowed)
    if unexpected:
        result["errors"].append(f"unexpected colors {unexpected}")

    wall_cols = [
        c for c in range(w) if all(grid[r][c] == 8 for r in range(h))
    ]
    wall_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if len(wall_cols) != 1:
        result["errors"].append(
            f"expected exactly one full-height color-8 wall, got columns {wall_cols}"
        )
    else:
        result["wall_col"] = wall_cols[0]
        if len(wall_cells) != h:
            result["errors"].append("color 8 must occur only on the full-height wall")

    markers = sorted(
        (r, c, grid[r][c])
        for r in range(h)
        for c in range(w)
        if grid[r][c] in _DIRECTIONS
    )
    result["markers"] = markers
    if not (2 <= len(markers) <= 3):
        result["errors"].append(
            f"expected 2-3 direction markers, got {len(markers)}"
        )
    if markers and len({value for _, _, value in markers}) < 2:
        result["errors"].append("expected at least two distinct marker directions")

    components = _all_components(grid)
    result["components"] = components
    if not (2 <= len(components) <= 3):
        result["errors"].append(
            f"expected 2-3 colored object components, got {len(components)}"
        )
    colors = [component["color"] for component in components]
    if len(colors) != len(set(colors)):
        result["errors"].append("each object must use a distinct color")
    for component in components:
        size = len(component["cells"])
        if not (3 <= size <= 4):
            result["errors"].append(
                f"color-{component['color']} object has {size} cells; expected 3-4"
            )

    component_by_cell: dict[tuple[int, int], int] = {}
    for index, component in enumerate(components):
        for cell in component["cells"]:
            component_by_cell[cell] = index

    object_marker_counts = [0 for _ in components]
    associations: list[dict[str, Any]] = []
    for mr, mc, marker in markers:
        adjacent_indices = {
            component_by_cell[(nr, nc)]
            for dr, dc in _CARDINAL
            for nr, nc in [(mr + dr, mc + dc)]
            if (nr, nc) in component_by_cell
        }
        if len(adjacent_indices) != 1:
            result["errors"].append(
                f"marker {marker} at {(mr, mc)} must touch exactly one object, "
                f"got {len(adjacent_indices)}"
            )
            continue
        component_index = next(iter(adjacent_indices))
        object_marker_counts[component_index] += 1
        component = components[component_index]
        dr, dc = _DIRECTIONS[marker]
        trailing = (mr + dr, mc + dc) in set(component["cells"])
        associations.append(
            {
                "marker": (mr, mc, marker),
                "component_index": component_index,
                "color": component["color"],
                "trailing": trailing,
            }
        )
    result["associations"] = associations

    for index, count in enumerate(object_marker_counts):
        color = components[index]["color"] if index < len(components) else "?"
        if count != 1:
            result["errors"].append(
                f"color-{color} object must have exactly one marker, got {count}"
            )
    if len(markers) != len(components):
        result["errors"].append("marker count must equal object count")
    return result


def _clear_markers(grid: list[list[int]]) -> list[list[int]]:
    output = [row[:] for row in grid]
    for r, c, value in [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in _DIRECTIONS
    ]:
        del value
        output[r][c] = 0
    return output


def _marker_adjacencies(
    grid: list[list[int]], marker: tuple[int, int, int]
) -> list[tuple[int, int]]:
    h, w = len(grid), len(grid[0])
    mr, mc, _ = marker
    return sorted(
        (nr, nc)
        for dr, dc in _CARDINAL
        for nr, nc in [(mr + dr, mc + dc)]
        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] not in (0, 8)
    )


def _slide_component(
    grid: list[list[int]],
    cells: list[tuple[int, int]],
    delta: tuple[int, int],
    *,
    max_steps: int | None = None,
) -> tuple[list[tuple[int, int]], int]:
    h, w = len(grid), len(grid[0])
    dr, dc = delta
    blockers = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0
    }
    current = list(cells)
    steps = 0
    while max_steps is None or steps < max_steps:
        nxt = [(r + dr, c + dc) for r, c in current]
        if any(
            not (0 <= r < h and 0 <= c < w) or (r, c) in blockers
            for r, c in nxt
        ):
            break
        current = nxt
        steps += 1
    return sorted(current), steps


DirectionFn = Callable[
    [tuple[int, int, int], list[list[int]], list[tuple[int, int]]],
    tuple[int, int],
]


def _simulate(
    grid: list[list[int]],
    *,
    reverse: bool = False,
    direction_fn: DirectionFn | None = None,
    max_steps: int | None = None,
) -> list[list[int]]:
    h, w, errors = _rectangular_grid(grid)
    if errors:
        raise ValueError("malformed grid: " + "; ".join(errors))
    del h, w
    markers = sorted(
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in _DIRECTIONS
    )
    if reverse:
        markers.reverse()
    output = _clear_markers(grid)

    for marker in markers:
        adjacent = _marker_adjacencies(output, marker)
        if not adjacent:
            continue
        cells = _component(output, adjacent[0])
        color = output[adjacent[0][0]][adjacent[0][1]]
        for r, c in cells:
            output[r][c] = 0
        delta = (
            direction_fn(marker, output, cells)
            if direction_fn is not None
            else _DIRECTIONS[marker[2]]
        )
        slid, _ = _slide_component(output, cells, delta, max_steps=max_steps)
        for r, c in slid:
            output[r][c] = color
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror of the pinned row-major Racket authority."""
    return _simulate(grid)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-linked input grammar, including canonical inputs."""
    del difficulty, meta
    analysis = _initial_analysis(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return sorted(set(reasons))
    try:
        if rule_mirror(grid) == _clear_markers(grid):
            reasons.append("the sequential slide rule must move at least one object")
    except Exception as exc:
        reasons.append(f"rule mirror failed: {type(exc).__name__}: {exc}")
    return sorted(set(reasons))


def strict_canonical_like(grid) -> list[str]:
    """Accept the canonical vertical-wall / marked-polyomino grammar."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _initial_analysis(grid)
    if analysis["errors"]:
        raise ValueError(
            "cannot observe axes on malformed grid: "
            + "; ".join(analysis["errors"])
        )
    wall_col = analysis["wall_col"]
    wall_position = (
        "edge" if wall_col in (0, analysis["w"] - 1) else "interior"
    )
    marker_attachment = (
        "trailing"
        if all(item["trailing"] for item in analysis["associations"])
        else "mixed"
    )
    return {
        "grid_h": analysis["h"],
        "grid_w": analysis["w"],
        "n_objects": len(analysis["components"]),
        "wall_position": wall_position,
        "marker_attachment": marker_attachment,
    }


def _direction_away_from_marker(
    marker: tuple[int, int, int],
    grid: list[list[int]],
    cells: list[tuple[int, int]],
) -> tuple[int, int]:
    del grid
    mr, mc, _ = marker
    adjacent = sorted(
        cell for cell in cells if abs(cell[0] - mr) + abs(cell[1] - mc) == 1
    )
    if not adjacent:
        return _DIRECTIONS[marker[2]]
    ar, ac = adjacent[0]
    return ar - mr, ac - mc


def _direction_toward_wall(
    marker: tuple[int, int, int],
    grid: list[list[int]],
    cells: list[tuple[int, int]],
) -> tuple[int, int]:
    del marker
    h, w = len(grid), len(grid[0])
    wall_cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if len(wall_cols) != 1:
        return (0, 0)
    wall_col = wall_cols[0]
    mean_col = sum(c for _, c in cells) / len(cells)
    return (0, 1) if mean_col < wall_col else (0, -1)


def _rival_move_away_from_marker(grid) -> list[list[int]]:
    return _simulate(grid, direction_fn=_direction_away_from_marker)


def _rival_move_toward_wall(grid) -> list[list[int]]:
    return _simulate(grid, direction_fn=_direction_toward_wall)


def _rival_reverse_scan_order(grid) -> list[list[int]]:
    return _simulate(grid, reverse=True)


def _rival_move_one_step(grid) -> list[list[int]]:
    return _simulate(grid, max_steps=1)


SEMANTIC_RIVALS: dict[
    str, Callable[[list[list[int]]], list[list[int]]]
] = {
    "move_away_from_marker": _rival_move_away_from_marker,
    "move_toward_wall": _rival_move_toward_wall,
    "reverse_scan_order": _rival_reverse_scan_order,
    "move_one_step": _rival_move_one_step,
}


def _rival_visible(
    grid: list[list[int]], rival: Callable[[list[list[int]]], list[list[int]]]
) -> bool:
    try:
        return not self_check(grid) and rival(grid) != rule_mirror(grid)
    except Exception:
        return False


SEMANTIC_WITNESSES = {
    "marker_attachment_color_key_visible": lambda grid: _rival_visible(
        grid, _rival_move_away_from_marker
    ),
    "wall_is_obstacle_not_destination": lambda grid: _rival_visible(
        grid, _rival_move_toward_wall
    ),
    "row_major_order_visible": lambda grid: _rival_visible(
        grid, _rival_reverse_scan_order
    ),
    "slide_until_blocked_visible": lambda grid: _rival_visible(
        grid, _rival_move_one_step
    ),
}

WITNESS_RIVALS = {
    "marker_attachment_color_key_visible": ["move_away_from_marker"],
    "wall_is_obstacle_not_destination": ["move_toward_wall"],
    "row_major_order_visible": ["reverse_scan_order"],
    "slide_until_blocked_visible": ["move_one_step"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# Every official marker lies directly behind its object, so this wrong rule is
# answer-equivalent on all public pairs.  The fourth schedule slot is the
# generated discriminator required to teach the marker-color key itself.
CANONICAL_SHORTCUTS = {
    "move_away_from_marker": _rival_move_away_from_marker,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require a four-demo lesson to determine direction, distance, and order."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) != EXAMPLES_NEEDED:
        return [f"expected exactly {EXAMPLES_NEEDED} demonstrations"]

    valid_demo_grids: list[list[list[int]]] = []
    marker_codes: set[int] = set()
    for index, pair in enumerate(demos):
        grid = pair.get("input") if isinstance(pair, dict) else None
        output = pair.get("output") if isinstance(pair, dict) else None
        errors = self_check(grid)
        if errors:
            reasons.append(f"demo {index} malformed: {'; '.join(errors)}")
            continue
        expected = rule_mirror(grid)
        if output != expected:
            reasons.append(f"demo {index} output does not match the pinned rule")
            continue
        valid_demo_grids.append(grid)
        marker_codes.update(
            value for row in grid for value in row if value in _DIRECTIONS
        )

    query_grid = query.get("input") if isinstance(query, dict) else None
    query_output = query.get("output") if isinstance(query, dict) else None
    query_errors = self_check(query_grid)
    if query_errors:
        reasons.append(f"query malformed: {'; '.join(query_errors)}")
    elif query_output != rule_mirror(query_grid):
        reasons.append("query output does not match the pinned rule")

    if marker_codes != {1, 2, 3, 4}:
        reasons.append(
            f"demos expose marker colors {sorted(marker_codes)}, not all 1..4"
        )
    required_witnesses = (
        "marker_attachment_color_key_visible",
        "row_major_order_visible",
        "wall_is_obstacle_not_destination",
        "slide_until_blocked_visible",
    )
    for name in required_witnesses:
        if not any(SEMANTIC_WITNESSES[name](grid) for grid in valid_demo_grids):
            reasons.append(f"demos contain no {name} counterexample")

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            if valid_demo_grids and all(
                competitor(grid) == rule_mirror(grid) for grid in valid_demo_grids
            ):
                reasons.append(f"competitor {name} fits every demonstration")
        except Exception as exc:
            reasons.append(
                f"competitor {name} raised {type(exc).__name__}: {exc}"
            )
    return reasons
