"""Generator for ordered waypoint routing through a wall maze.

The input contains color-1 walls, color-0 corridors, start marker 2, end
marker 3, and one to four distinct intermediate markers chosen from 4..7.
Visit intermediate markers in ascending color order.  For every consecutive
pair, run four-neighbor BFS with neighbor order up, down, left, right while
blocking color 1.  Paint only traversed color-0 cells with color 8 and preserve
walls and markers.

The generator deliberately constructs examples that distinguish the rule from
ignoring walls, connecting only 2 to 3, reversing waypoint order, and ordering
waypoints by position.  A four-example schedule covers 1, 2, 3, and 4 mids and
includes a canonical-size scene in every lesson.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx

Grid = list[list[int]]
Cell = tuple[int, int]

GENERATOR_ID = "dbee38495261"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "f1fa88aeec11"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A color-1 wall maze contains start 2, end 3, and one to four distinct "
    "waypoints from colors 4..7. Visit present waypoints in ascending numeric "
    "order between 2 and 3. For each leg, take the deterministic shortest "
    "four-neighbor path through non-wall cells (neighbor order up, down, left, "
    "right) and paint only path cells that were color 0 with color 8. Preserve "
    "all walls and markers."
)

INVARIANTS = [
    "the rectangular border is color 1 and the input palette is a subset of 0..7",
    "colors 2 and 3 occur exactly once",
    "one to four colors from 4..7 occur exactly once each",
    "every consecutive ascending-color waypoint leg is connected through non-walls",
    "an intended leg does not pass through a different marker",
    "the intended output paints at least one zero and leaves at least one zero",
    "generated scenes distinguish wall-aware routing from wall-ignoring routing",
    "the four-scene schedule distinguishes numeric waypoint order from shortcuts",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchor or difficulty-aware draw",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchor or difficulty-aware draw",
        "valid": "9..16",
    },
    "n_mids": {
        "type": "int",
        "default": "deterministic four-scene schedule",
        "valid": "1..4",
    },
}

_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_SHAPES = ((7, 9), (8, 9), (8, 10))

# Deterministic, verified fallback scenes.  The final row of each 8x9 probe was
# redundant wall padding, so these are the minimal 7x9 versions.  Larger exact
# requests embed the scene in an all-wall canvas without changing its rule.
_FALLBACK_ROWS = {
    1: (
        "111111111",
        "101000001",
        "101011101",
        "120004001",
        "101011101",
        "100310001",
        "111111111",
    ),
    2: (
        "111111111",
        "160000101",
        "101000101",
        "101410101",
        "101010101",
        "100310021",
        "111111111",
    ),
    3: (
        "111111111",
        "150000001",
        "111011011",
        "170014001",
        "101110101",
        "100003021",
        "111111111",
    ),
    4: (
        "111111111",
        "161503101",
        "101010101",
        "100000071",
        "101111101",
        "100400021",
        "111111111",
    ),
}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")


def _draw_axis(
    ctx,
    label: str,
    valid_lo: int,
    valid_hi: int,
    default_lo: int,
    default_hi: int,
) -> int:
    """Draw an exact axis while letting an override use its whole domain."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, valid_lo, valid_hi)
    return ctx.draw_int_strict(label, default_lo, default_hi)


def _profile_shape(ctx, profile: int, difficulty: str | None) -> tuple[int, int]:
    if profile == 0:
        height, width = ctx.draw_rng("canonical_shape").choice(_CANONICAL_SHAPES)
        return (
            _draw_axis(ctx, "grid_h", 7, 14, height, height),
            _draw_axis(ctx, "grid_w", 9, 16, width, width),
        )

    bounds = {
        None: {
            1: (7, 9, 9, 11),
            2: (9, 12, 11, 14),
            3: (12, 14, 14, 16),
        },
        "easy": {
            1: (7, 8, 9, 10),
            2: (8, 9, 10, 11),
            3: (9, 10, 11, 12),
        },
        "medium": {
            1: (8, 9, 10, 11),
            2: (9, 11, 11, 13),
            3: (11, 12, 13, 14),
        },
        "hard": {
            1: (10, 11, 12, 13),
            2: (11, 13, 13, 15),
            3: (13, 14, 15, 16),
        },
    }[difficulty][profile]
    h_lo, h_hi, w_lo, w_hi = bounds
    return (
        _draw_axis(ctx, "grid_h", 7, 14, h_lo, h_hi),
        _draw_axis(ctx, "grid_w", 9, 16, w_lo, w_hi),
    )


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = int(sample_index) % EXAMPLES_NEEDED
    height, width = _profile_shape(ctx, profile, difficulty)
    n_mids = _draw_axis(ctx, "n_mids", 1, 4, profile + 1, profile + 1)
    return _construct_scene(
        height,
        width,
        n_mids,
        ctx.draw_rng("maze_and_markers"),
        profile=profile,
    )


def _carve_maze(height: int, width: int, rng, loops: int) -> Grid:
    grid = [[1 for _ in range(width)] for _ in range(height)]
    rooms = {
        (row, col)
        for row in range(1, height - 1, 2)
        for col in range(1, width - 1, 2)
    }
    if not rooms:
        return grid
    start = rng.choice(sorted(rooms))
    grid[start[0]][start[1]] = 0
    seen = {start}
    stack = [start]
    while stack:
        row, col = stack[-1]
        options = []
        for delta_row, delta_col in _NEIGHBORS:
            nxt = (row + 2 * delta_row, col + 2 * delta_col)
            if nxt in rooms and nxt not in seen:
                options.append((nxt, delta_row, delta_col))
        if not options:
            stack.pop()
            continue
        nxt, delta_row, delta_col = rng.choice(options)
        grid[row + delta_row][col + delta_col] = 0
        grid[nxt[0]][nxt[1]] = 0
        seen.add(nxt)
        stack.append(nxt)

    connectors = []
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 1:
                continue
            vertical = grid[row - 1][col] == 0 and grid[row + 1][col] == 0
            horizontal = grid[row][col - 1] == 0 and grid[row][col + 1] == 0
            if vertical or horizontal:
                connectors.append((row, col))
    rng.shuffle(connectors)
    for row, col in connectors[:loops]:
        grid[row][col] = 0
    return grid


def _construct_scene(height: int, width: int, n_mids: int, rng, *, profile: int) -> Grid:
    loops = max(2, min(7, (height * width) // 25 + profile // 2))
    for _maze_attempt in range(12):
        base = _carve_maze(height, width, rng, loops)
        rooms = [
            (row, col)
            for row in range(1, height - 1, 2)
            for col in range(1, width - 1, 2)
            if base[row][col] == 0
        ]
        if len(rooms) < n_mids + 2:
            continue
        mids = rng.sample([4, 5, 6, 7], n_mids)
        marker_colors = [2, *mids, 3]
        intended_order = [2, *sorted(mids), 3]
        for _placement_attempt in range(600):
            locations = rng.sample(rooms, len(marker_colors))
            grid = [row[:] for row in base]
            for color, (row, col) in zip(marker_colors, locations):
                grid[row][col] = color
            if not _clean_intended_legs(grid, intended_order):
                continue
            if _scene_separates_competitors(grid, n_mids):
                return grid
    return _fallback_scene(height, width, n_mids)


def _fallback_scene(height: int, width: int, n_mids: int) -> Grid:
    grid = [[1 for _ in range(width)] for _ in range(height)]
    rows = _FALLBACK_ROWS[n_mids]
    for row_index, text in enumerate(rows):
        for col_index, value in enumerate(text):
            grid[row_index][col_index] = int(value)
    return grid


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be nonempty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular with list rows"]
    errors: list[str] = []
    if len(grid) > 30 or width > 30:
        errors.append(f"grid exceeds ARC limit: {len(grid)}x{width}")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid values must be integer colors 0..9 (not bool)")
    return errors


def _positions(grid: Grid) -> dict[int, Cell]:
    return {
        value: (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if 2 <= value <= 7
    }


def _all_positions(grid: Grid, color: int) -> list[Cell]:
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]


def _visit_order(grid: Grid) -> list[int]:
    present = {value for row in grid for value in row}
    return [2, *[color for color in (4, 5, 6, 7) if color in present], 3]


def _bfs(grid: Grid, start: Cell, goal: Cell, *, ignore_walls: bool = False) -> list[Cell]:
    height, width = len(grid), len(grid[0])
    queue: deque[Cell] = deque([start])
    previous: dict[Cell, Cell | None] = {start: None}
    while queue:
        cell = queue.popleft()
        if cell == goal:
            break
        for delta_row, delta_col in _NEIGHBORS:
            nxt = (cell[0] + delta_row, cell[1] + delta_col)
            if not (0 <= nxt[0] < height and 0 <= nxt[1] < width):
                continue
            if nxt in previous:
                continue
            if not ignore_walls and grid[nxt[0]][nxt[1]] == 1:
                continue
            previous[nxt] = cell
            queue.append(nxt)
    if goal not in previous:
        return []
    path: list[Cell] = []
    cursor: Cell | None = goal
    while cursor is not None:
        path.append(cursor)
        cursor = previous[cursor]
    path.reverse()
    return path


def _solve_order(grid: Grid, order: Iterable[int], *, ignore_walls: bool = False) -> Grid:
    ordered = list(order)
    positions = _positions(grid)
    output = [row[:] for row in grid]
    for first, second in zip(ordered, ordered[1:]):
        if first not in positions or second not in positions:
            raise ValueError(f"missing marker for leg {first}->{second}")
        path = _bfs(grid, positions[first], positions[second], ignore_walls=ignore_walls)
        if not path:
            raise ValueError(f"disconnected leg {first}->{second}")
        for row, col in path[1:-1]:
            if output[row][col] == 0:
                output[row][col] = 8
    return output


def rule_mirror(grid: Grid) -> Grid:
    """Independent Python audit mirror; the selected Racket rule is authority."""
    return _solve_order(grid, _visit_order(grid))


def _rival_ignore_walls(grid: Grid) -> Grid:
    try:
        return _solve_order(grid, _visit_order(grid), ignore_walls=True)
    except (KeyError, ValueError):
        return [row[:] for row in grid]


def _rival_direct(grid: Grid) -> Grid:
    try:
        return _solve_order(grid, (2, 3))
    except (KeyError, ValueError):
        return [row[:] for row in grid]


def _rival_reverse(grid: Grid) -> Grid:
    mids = list(reversed(_visit_order(grid)[1:-1]))
    try:
        return _solve_order(grid, [2, *mids, 3])
    except (KeyError, ValueError):
        return [row[:] for row in grid]


def _rival_row_major(grid: Grid) -> Grid:
    positions = _positions(grid)
    mids = sorted(
        (color for color in (4, 5, 6, 7) if color in positions),
        key=lambda color: positions[color],
    )
    try:
        return _solve_order(grid, [2, *mids, 3])
    except (KeyError, ValueError):
        return [row[:] for row in grid]


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "ignore walls": _rival_ignore_walls,
    "connect only start to end": _rival_direct,
    "visit mids in reverse numeric order": _rival_reverse,
    "visit mids in row-major order": _rival_row_major,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
SCENE_COMPETITORS = {
    "ignore walls": _rival_ignore_walls,
    "connect only start to end": _rival_direct,
}


def _witness_wall_detour(grid: Grid) -> bool:
    try:
        return _rival_ignore_walls(grid) != rule_mirror(grid)
    except (KeyError, ValueError, TypeError):
        return False


def _witness_waypoint_required(grid: Grid) -> bool:
    try:
        return _rival_direct(grid) != rule_mirror(grid)
    except (KeyError, ValueError, TypeError):
        return False


def _witness_numeric_order(grid: Grid) -> bool:
    try:
        return len(_visit_order(grid)) >= 5 and _rival_reverse(grid) != rule_mirror(grid)
    except (KeyError, ValueError, TypeError):
        return False


def _witness_not_row_major(grid: Grid) -> bool:
    try:
        return len(_visit_order(grid)) >= 5 and _rival_row_major(grid) != rule_mirror(grid)
    except (KeyError, ValueError, TypeError):
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "wall detour": _witness_wall_detour,
    "waypoint required": _witness_waypoint_required,
    "numeric waypoint order": _witness_numeric_order,
    "numeric order differs from row-major": _witness_not_row_major,
}
WITNESS_RIVALS = {
    "wall detour": ["ignore walls"],
    "waypoint required": ["connect only start to end"],
    "numeric waypoint order": ["visit mids in reverse numeric order"],
    "numeric order differs from row-major": ["visit mids in row-major order"],
}


def _clean_intended_legs(grid: Grid, order: list[int]) -> bool:
    positions = _positions(grid)
    marker_cells = set(positions.values())
    for first, second in zip(order, order[1:]):
        path = _bfs(grid, positions[first], positions[second])
        if len(path) < 4:
            return False
        if set(path[1:-1]) & (marker_cells - {positions[first], positions[second]}):
            return False
    return True


def _scene_separates_competitors(grid: Grid, n_mids: int) -> bool:
    try:
        expected = rule_mirror(grid)
    except ValueError:
        return False
    if expected == grid:
        return False
    if not any(value == 0 for row in expected for value in row):
        return False
    if _rival_ignore_walls(grid) == expected or _rival_direct(grid) == expected:
        return False
    if n_mids >= 2:
        if _rival_reverse(grid) == expected or _rival_row_major(grid) == expected:
            return False
    return True


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _shape_errors(grid)
    if errors:
        return {"errors": errors}
    assert isinstance(grid, list)
    height, width = len(grid), len(grid[0])
    values = [value for row in grid for value in row]
    counts = Counter(values)
    errors = []
    unexpected = sorted(set(values) - set(range(8)))
    if unexpected:
        errors.append(f"unexpected input colors: {unexpected}")
    if counts[0] == 0:
        errors.append("input must contain open color-0 corridor cells")
    if counts[1] == 0:
        errors.append("input must contain color-1 wall cells")
    for endpoint in (2, 3):
        if counts[endpoint] != 1:
            errors.append(
                f"expected exactly one color-{endpoint} marker, found {counts[endpoint]}"
            )
    mids = [color for color in (4, 5, 6, 7) if counts[color]]
    if not 1 <= len(mids) <= 4:
        errors.append(f"expected 1..4 distinct mid markers, found {len(mids)}")
    for color in mids:
        if counts[color] != 1:
            errors.append(f"mid marker color {color} appears {counts[color]} times")
    border = (
        list(grid[0])
        + list(grid[-1])
        + [row[0] for row in grid[1:-1]]
        + [row[-1] for row in grid[1:-1]]
    )
    if border and any(value != 1 for value in border):
        errors.append("all border cells must be color-1 walls")

    positions = _positions(grid)
    order = [2, *mids, 3]
    path_cells: set[Cell] = set()
    marker_cells = set(positions.values())
    if not any("expected exactly one" in error for error in errors):
        for first, second in zip(order, order[1:]):
            if first not in positions or second not in positions:
                continue
            path = _bfs(grid, positions[first], positions[second])
            if not path:
                errors.append(f"intended leg {first}->{second} is disconnected")
                continue
            crossed = set(path[1:-1]) & (
                marker_cells - {positions[first], positions[second]}
            )
            if crossed:
                errors.append(f"intended leg {first}->{second} crosses another marker")
            path_cells.update(path)
    painted = {
        cell
        for cell in path_cells
        if grid[cell[0]][cell[1]] == 0
    }
    zero_cells = {
        (row, col)
        for row, values_row in enumerate(grid)
        for col, value in enumerate(values_row)
        if value == 0
    }
    if positions and not errors:
        if not painted:
            errors.append("intended route must paint at least one color-0 cell")
        if not (zero_cells - painted):
            errors.append("intended route must leave at least one color-0 cell unpainted")
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "counts": counts,
        "mids": mids,
        "path_cells": path_cells,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return actionable structural/rule errors without raising on bad input."""
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Generated and canonical inputs share the same checked maze manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid grid: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_mids": len(analysis["mids"]),
    }


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a declared rival fits demos but changes query."""
    reasons: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["lesson must contain at least one labeled demonstration"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must be a labeled input/output pair"]
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not a labeled input/output pair")
            continue
        if self_check(pair["input"]):
            reasons.append(f"demo {index} is outside the canonical maze manifold")
        try:
            if rule_mirror(pair["input"]) != pair["output"]:
                reasons.append(f"demo {index} output does not match the selected rule")
        except (TypeError, ValueError):
            reasons.append(f"demo {index} cannot be solved by the selected rule")
    if self_check(query["input"]):
        reasons.append("query is outside the canonical maze manifold")
    try:
        if rule_mirror(query["input"]) != query["output"]:
            reasons.append("query output does not match the selected rule")
    except (TypeError, ValueError):
        reasons.append("query cannot be solved by the selected rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if fits_demos and rival(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} fits every demonstration but changes the query"
            )
    return reasons
