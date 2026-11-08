"""Generator for ``Ordered Waypoint Path``.

The input is a wall maze (8) with a start marker (2), end marker (3), and
ordered checkpoints 4, 5, and optionally 6.  The selected Racket authority
paints zero cells on the unique shortest path for each consecutive leg
``2 -> 4 -> 5 -> [6] -> 3`` with color 7.

Generated mazes use a two-rail ladder with three rungs.  The topology contains
real cycles, but every intended leg has one shortest path.  Each scene also
separates the intended rule from direct 2-to-3, reverse-checkpoint, row-major,
identity, and paint-all-open shortcuts.
"""
from __future__ import annotations

from collections import Counter, deque
from functools import lru_cache
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]
Cell = tuple[int, int]

GENERATOR_ID = "df17e660cb8e"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "966f58dd55e6"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A border-walled maze uses color 8 for walls and color 0 for open cells. "
    "It contains exactly one start marker 2, one end marker 3, checkpoints 4 "
    "and 5, and optionally checkpoint 6. Visit markers in numeric order "
    "2 -> 4 -> 5 -> [6] -> 3. For each consecutive pair, take its unique "
    "shortest four-neighbor path through non-8 cells and paint only the zero "
    "cells on the combined path color 7. Preserve walls and all markers."
)

INVARIANTS = [
    "all border cells are wall color 8",
    "the input palette is {0,2,3,4,5,8} or {0,2,3,4,5,6,8}",
    "markers 2, 3, 4, and 5 occur exactly once; marker 6 is optional once",
    "all non-wall cells form one four-connected corridor component",
    "every consecutive numeric waypoint leg has exactly one shortest path",
    "an intended leg never passes through a different marker",
    "the ordered waypoint answer differs from direct and reverse routes",
    "the orientation schedule falsifies row-major ordering at lesson level",
    "at least one open zero is painted and at least one remains unpainted",
]

ORIENTATIONS = ("identity", "flip_h", "flip_v", "rot180")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchor or difficulty-aware draw",
        "valid": "9..15",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchor or difficulty-aware draw",
        "valid": "11..19",
    },
    "n_intermediates": {
        "type": "int",
        "default": "canonical anchor or difficulty-aware draw",
        "valid": "2..3",
    },
    "orientation": {
        "type": "str",
        "default": "four-way deterministic schedule",
        "valid": "|".join(ORIENTATIONS),
    },
}

_CANONICAL_PROFILES = ((9, 11, 2), (9, 12, 2), (9, 13, 2), (9, 11, 3))
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")


def _draw_int_axis(ctx, label: str, lo: int, hi: int, fixed: int | None) -> int:
    if fixed is not None:
        return ctx.draw_int(label, fixed, fixed)
    return ctx.draw_int_diff(label, lo, hi)


def _draw_choice_axis(ctx, label: str, options: tuple[str, ...], fixed: str | None) -> str:
    if fixed is not None:
        return ctx.draw_choice(label, (fixed,))
    return ctx.draw_choice(label, options)


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid is empty or not a list"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["first row is empty or not a list"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid is ragged or contains a non-list row"]
    errors: list[str] = []
    height = len(grid)
    if height > 30 or width > 30:
        errors.append(f"grid exceeds ARC limit: {height}x{width}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or color outside 0..9")
    return errors


def _marker_positions(grid: Grid) -> dict[int, Cell]:
    positions: dict[int, Cell] = {}
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if 2 <= value <= 7 and value not in positions:
                positions[value] = (row_index, col_index)
    return positions


def _all_positions(grid: Grid, color: int) -> list[Cell]:
    return [
        (row_index, col_index)
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value == color
    ]


def _shortest_path(grid: Grid, start: Cell, goal: Cell) -> tuple[list[Cell], int]:
    """Return one shortest path and the number of shortest paths."""
    height, width = len(grid), len(grid[0])
    distance = {start: 0}
    count = {start: 1}
    previous: dict[Cell, Cell] = {}
    queue: deque[Cell] = deque([start])
    while queue:
        row, col = queue.popleft()
        for delta_row, delta_col in _NEIGHBORS:
            nxt = (row + delta_row, col + delta_col)
            if not (0 <= nxt[0] < height and 0 <= nxt[1] < width):
                continue
            if grid[nxt[0]][nxt[1]] == 8:
                continue
            candidate_distance = distance[(row, col)] + 1
            if nxt not in distance:
                distance[nxt] = candidate_distance
                count[nxt] = count[(row, col)]
                previous[nxt] = (row, col)
                queue.append(nxt)
            elif distance[nxt] == candidate_distance:
                count[nxt] += count[(row, col)]
    if goal not in distance:
        return [], 0
    path: list[Cell] = []
    if count[goal] == 1:
        current = goal
        while current != start:
            path.append(current)
            current = previous[current]
        path.append(start)
        path.reverse()
    return path, count[goal]


def _visit_colors(grid: Grid) -> list[int]:
    colors = {value for row in grid for value in row}
    intermediates = [color for color in (4, 5, 6) if color in colors]
    return [2, *intermediates, 3]


def _path_union(grid: Grid, colors: Iterable[int]) -> tuple[set[Cell], list[str]]:
    ordered = list(colors)
    positions = _marker_positions(grid)
    union: set[Cell] = set()
    errors: list[str] = []
    marker_cells = set(positions.values())
    for first, second in zip(ordered, ordered[1:]):
        if first not in positions or second not in positions:
            errors.append(f"missing marker for leg {first}->{second}")
            continue
        path, count = _shortest_path(grid, positions[first], positions[second])
        if count == 0:
            errors.append(f"leg {first}->{second} is disconnected")
            continue
        if count != 1:
            errors.append(f"leg {first}->{second} has {count} shortest paths")
            continue
        crossed = (set(path[1:-1]) & marker_cells) - {
            positions[first],
            positions[second],
        }
        if crossed:
            errors.append(f"leg {first}->{second} crosses another marker")
        union.update(path)
    return union, errors


def _paint_cells(grid: Grid, cells: Iterable[Cell], color: int = 7) -> Grid:
    output = [row[:] for row in grid]
    for row, col in cells:
        if grid[row][col] == 0:
            output[row][col] = color
    return output


def rule_mirror(grid: Grid) -> Grid:
    """Independent Python audit mirror; Racket remains the output authority."""
    path_cells, errors = _path_union(grid, _visit_colors(grid))
    if errors:
        raise ValueError("; ".join(errors))
    return _paint_cells(grid, path_cells)


def _rival_identity(grid: Grid) -> Grid:
    return [row[:] for row in grid]


def _rival_direct(grid: Grid) -> Grid:
    path_cells, errors = _path_union(grid, (2, 3))
    return [row[:] for row in grid] if errors else _paint_cells(grid, path_cells)


def _rival_reverse(grid: Grid) -> Grid:
    intermediates = list(reversed(_visit_colors(grid)[1:-1]))
    path_cells, errors = _path_union(grid, [2, *intermediates, 3])
    return [row[:] for row in grid] if errors else _paint_cells(grid, path_cells)


def _rival_row_major(grid: Grid) -> Grid:
    positions = _marker_positions(grid)
    intermediates = sorted(
        (color for color in (4, 5, 6) if color in positions),
        key=lambda color: positions[color],
    )
    path_cells, errors = _path_union(grid, [2, *intermediates, 3])
    return [row[:] for row in grid] if errors else _paint_cells(grid, path_cells)


def _rival_paint_all_open(grid: Grid) -> Grid:
    return [[7 if value == 0 else value for value in row] for row in grid]


def _rival_paint_five(grid: Grid) -> Grid:
    path_cells, errors = _path_union(grid, _visit_colors(grid))
    return [row[:] for row in grid] if errors else _paint_cells(grid, path_cells, 5)


LESSON_COMPETITORS: dict[str, Callable[[Grid], Grid]] = {
    "copy input unchanged": _rival_identity,
    "connect only start to end": _rival_direct,
    "visit checkpoints in reverse numeric order": _rival_reverse,
    "visit checkpoints in row-major order": _rival_row_major,
    "paint every open cell": _rival_paint_all_open,
    "paint the route color 5": _rival_paint_five,
}
SEMANTIC_RIVALS = LESSON_COMPETITORS
SCENE_COMPETITORS = {
    name: competitor
    for name, competitor in LESSON_COMPETITORS.items()
    if name != "visit checkpoints in row-major order"
}


def _connected_nonwalls(grid: Grid) -> bool:
    cells = {
        (row_index, col_index)
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value != 8
    }
    if not cells:
        return False
    reached = {next(iter(cells))}
    queue = deque(reached)
    while queue:
        row, col = queue.popleft()
        for delta_row, delta_col in _NEIGHBORS:
            nxt = (row + delta_row, col + delta_col)
            if nxt in cells and nxt not in reached:
                reached.add(nxt)
                queue.append(nxt)
    return reached == cells


def _cycle_rank(grid: Grid) -> int:
    cells = {
        (row_index, col_index)
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value != 8
    }
    edges = sum(
        (row + 1, col) in cells for row, col in cells
    ) + sum((row, col + 1) in cells for row, col in cells)
    return edges - len(cells) + 1 if cells else 0


def _orientation_from_markers(grid: Grid) -> str:
    positions = _marker_positions(grid)
    n_intermediates = 3 if 6 in positions else 2
    if n_intermediates == 2:
        start, four, five, end = (
            positions[2], positions[4], positions[5], positions[3]
        )
        vertical_flip = start[0] > four[0]
        horizontal_flip = not (start[1] < end[1] < five[1])
    else:
        start, four, five, six, end = (
            positions[2], positions[4], positions[5], positions[6], positions[3]
        )
        vertical_flip = start[0] < five[0]
        horizontal_flip = not (four[1] < start[1] < end[1])
        if four[1] != five[1] or start[1] != six[1]:
            raise ValueError("marker columns do not match a supported ladder orientation")
    if vertical_flip and horizontal_flip:
        return "rot180"
    if vertical_flip:
        return "flip_v"
    if horizontal_flip:
        return "flip_h"
    return "identity"


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _shape_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    palette = {value for row in grid for value in row}
    counts = Counter(value for row in grid for value in row)
    marker_counts = {color: len(_all_positions(grid, color)) for color in range(2, 8)}
    order = _visit_colors(grid)
    path_cells, path_errors = _path_union(grid, order)
    output = _paint_cells(grid, path_cells) if not path_errors else None
    zero_cells = {
        (row_index, col_index)
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value == 0
    }
    painted_zero = zero_cells & path_cells
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": palette,
        "counts": counts,
        "marker_counts": marker_counts,
        "order": order,
        "path_cells": path_cells,
        "path_errors": path_errors,
        "painted_zero": painted_zero,
        "unpainted_zero": zero_cells - path_cells,
        "connected": _connected_nonwalls(grid),
        "cycle_rank": _cycle_rank(grid),
        "output": output,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-compatible maze grammar and unique path legs."""
    del difficulty
    info = _analysis(grid)
    errors = list(info.get("errors", []))
    if errors:
        return errors

    height, width = info["height"], info["width"]
    if not (9 <= height <= 15):
        errors.append(f"height {height} outside supported range 9..15")
    if not (11 <= width <= 19):
        errors.append(f"width {width} outside supported range 11..19")
    if any(value != 8 for value in grid[0] + grid[-1]):
        errors.append("top or bottom border contains a non-wall cell")
    if any(row[0] != 8 or row[-1] != 8 for row in grid):
        errors.append("left or right border contains a non-wall cell")

    expected_palettes = ({0, 2, 3, 4, 5, 8}, {0, 2, 3, 4, 5, 6, 8})
    if info["palette"] not in expected_palettes:
        errors.append(f"unexpected input palette {sorted(info['palette'])}")
    expected_markers = (2, 3, 4, 5) + ((6,) if 6 in info["palette"] else ())
    for color in expected_markers:
        if info["marker_counts"][color] != 1:
            errors.append(
                f"expected exactly one marker {color}, found {info['marker_counts'][color]}"
            )
    for color in (7,):
        if info["marker_counts"][color] != 0:
            errors.append("input must not contain route color 7")
    if not info["connected"]:
        errors.append("non-wall corridor cells are not one connected component")
    if info["counts"][8] <= sum(info["counts"].values()) - info["counts"][8]:
        errors.append("wall color 8 is not the modal background")
    errors.extend(info["path_errors"])
    if not info["painted_zero"]:
        errors.append("ordered route paints no zero cells")
    if not info["unpainted_zero"]:
        errors.append("ordered route consumes every open zero cell")

    if meta and isinstance(meta, dict) and not meta.get("canonical"):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict) and not errors:
            observed = observe_overrides(grid)
            for axis, value in requested.items():
                if axis in AXES and observed.get(axis) != value:
                    errors.append(
                        f"{axis} requested {value!r}, observed {observed.get(axis)!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept the complete oracle-valid task manifold, including canonical scenes.

    Pedagogical rival-killing constraints belong to generated-scene checks and
    lesson windows; canonical examples must not be disowned merely because one
    example alone underdetermines checkpoint order.
    """
    return list(self_check(grid))


def _generated_scene_errors(grid: Grid) -> list[str]:
    errors = list(strict_canonical_like(grid))
    if errors:
        return errors
    info = _analysis(grid)
    if info["cycle_rank"] < 1:
        errors.append("maze has no cycle, so shortest-path choice is not demonstrated")
    intended = info["output"]
    for name, competitor in SCENE_COMPETITORS.items():
        if competitor(grid) == intended:
            errors.append(f"scene does not refute shortcut: {name}")
    return errors


def observe_overrides(grid: Grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_intermediates": 3 if any(6 in row for row in grid) else 2,
        "orientation": _orientation_from_markers(grid),
    }


def _semantic_info(grid: Grid) -> dict[str, Any] | None:
    return None if strict_canonical_like(grid) else _analysis(grid)


SEMANTIC_WITNESSES = {
    "unique_shortest_waypoint_legs": lambda grid: bool(
        (info := _semantic_info(grid)) and not info["path_errors"]
    ),
    "waypoints_change_direct_answer": lambda grid: bool(
        (info := _semantic_info(grid)) and _rival_direct(grid) != info["output"]
    ),
    "numeric_order_differs_from_row_major": lambda grid: bool(
        (info := _semantic_info(grid)) and _rival_row_major(grid) != info["output"]
    ),
    "reverse_order_changes_answer": lambda grid: bool(
        (info := _semantic_info(grid)) and _rival_reverse(grid) != info["output"]
    ),
    "unvisited_corridor_remains_zero": lambda grid: bool(
        (info := _semantic_info(grid)) and info["unpainted_zero"]
    ),
    "two_intermediate_scene": lambda grid: bool(
        (info := _semantic_info(grid)) and 6 not in info["palette"]
    ),
    "three_intermediate_scene": lambda grid: bool(
        (info := _semantic_info(grid)) and 6 in info["palette"]
    ),
    **{
        f"orientation_{orientation}": (
            lambda grid, expected=orientation: not strict_canonical_like(grid)
            and observe_overrides(grid)["orientation"] == expected
        )
        for orientation in ORIENTATIONS
    },
}


WITNESS_RIVALS = {
    "unique_shortest_waypoint_legs": ["copy input unchanged"],
    "waypoints_change_direct_answer": ["connect only start to end"],
    "numeric_order_differs_from_row_major": [
        "visit checkpoints in row-major order"
    ],
    "reverse_order_changes_answer": [
        "visit checkpoints in reverse numeric order"
    ],
    "unvisited_corridor_remains_zero": ["paint every open cell"],
    "two_intermediate_scene": ["connect only start to end"],
    "three_intermediate_scene": ["connect only start to end"],
    "orientation_identity": ["connect only start to end"],
    "orientation_flip_h": ["connect only start to end"],
    "orientation_flip_v": ["connect only start to end"],
    "orientation_rot180": ["connect only start to end"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject an episode when a named shortcut survives demos but changes query."""
    errors: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"{role} is not an input/output pair")
            continue
        findings = strict_canonical_like(pair["input"])
        if findings:
            errors.append(f"{role} is not lawful: {findings[:2]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            errors.append(f"{role} output disagrees with ordered waypoint rule")
    if errors:
        return errors

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo["output"] for demo in demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            errors.append(f"demos do not falsify shortcut '{name}'")
    return errors


def _abstract_graph(
    rungs: tuple[int, ...], gaps: tuple[int, int, int], vertical: int
) -> dict[tuple[int, int], list[tuple[tuple[int, int], int]]]:
    graph = {(rail, column): [] for rail in (0, 1) for column in range(4)}
    for rail in (0, 1):
        for column, weight in enumerate(gaps):
            first, second = (rail, column), (rail, column + 1)
            graph[first].append((second, weight))
            graph[second].append((first, weight))
    for column in rungs:
        first, second = (0, column), (1, column)
        graph[first].append((second, vertical))
        graph[second].append((first, vertical))
    return graph


def _abstract_path(
    graph: dict[tuple[int, int], list[tuple[tuple[int, int], int]]],
    start: tuple[int, int],
    goal: tuple[int, int],
) -> tuple[set[tuple[tuple[int, int], tuple[int, int]]], int]:
    distance = {start: 0}
    count = {start: 1}
    previous: dict[tuple[int, int], tuple[int, int]] = {}
    queue: list[tuple[int, tuple[int, int]]] = [(0, start)]
    while queue:
        queue.sort(reverse=True)
        current_distance, current = queue.pop()
        if current_distance != distance[current]:
            continue
        for neighbor, weight in graph[current]:
            candidate = current_distance + weight
            if candidate < distance.get(neighbor, 10**9):
                distance[neighbor] = candidate
                count[neighbor] = count[current]
                previous[neighbor] = current
                queue.append((candidate, neighbor))
            elif candidate == distance.get(neighbor):
                count[neighbor] = count.get(neighbor, 0) + count[current]
    if goal not in distance or count[goal] != 1:
        return set(), count.get(goal, 0)
    edges = set()
    current = goal
    while current != start:
        parent = previous[current]
        edges.add(tuple(sorted((parent, current))))
        current = parent
    return edges, 1


def _abstract_union(
    graph: dict[tuple[int, int], list[tuple[tuple[int, int], int]]],
    order: list[tuple[int, int]],
) -> tuple[set[tuple[tuple[int, int], tuple[int, int]]], bool]:
    union = set()
    marker_nodes = set(order)
    for first, second in zip(order, order[1:]):
        edges, count = _abstract_path(graph, first, second)
        if count != 1:
            return set(), False
        union.update(edges)
        # In this ladder family, marker-crossing can only happen at a marker node
        # lying on the edge path. The concrete self-check catches any regression.
        if not edges and first != second:
            return set(), False
    return union, bool(marker_nodes)


def _base_spec(n_intermediates: int) -> tuple[tuple[int, ...], list[tuple[int, int]]]:
    if n_intermediates == 2:
        # S top-c1, 4 bottom-c2, 5 top-c3, E top-c2.
        return (0, 1, 3), [(0, 1), (1, 2), (0, 3), (0, 2)]
    # S bottom-c1, 4 bottom-c0, 5 top-c0, 6 top-c1, E bottom-c2.
    return (0, 2, 3), [(1, 1), (1, 0), (0, 0), (0, 1), (1, 2)]


@lru_cache(maxsize=None)
def _valid_gap_splits(
    n_intermediates: int, height: int, width: int
) -> tuple[tuple[int, int, int], ...]:
    total = width - 3
    # Markers live on one-cell leaf spurs outside the two rails, so the
    # rail-to-rail rung length is the interior distance between rows 2 and h-3.
    vertical = height - 5
    rungs, order = _base_spec(n_intermediates)
    valid: list[tuple[int, int, int]] = []
    for first in range(2, total - 3):
        for second in range(2, total - first - 1):
            third = total - first - second
            if third < 2:
                continue
            gaps = (first, second, third)
            graph = _abstract_graph(rungs, gaps, vertical)
            intended, okay = _abstract_union(graph, order)
            if not okay:
                continue
            direct, direct_ok = _abstract_union(graph, [order[0], order[-1]])
            reverse, reverse_ok = _abstract_union(
                graph, [order[0], *reversed(order[1:-1]), order[-1]]
            )
            row_major, row_major_ok = _abstract_union(
                graph, [order[0], *sorted(order[1:-1]), order[-1]]
            )
            if (
                direct_ok
                and reverse_ok
                and row_major_ok
                and intended != direct
                and intended != reverse
                and intended != row_major
            ):
                valid.append(gaps)
    return tuple(valid)


def _carve_segment(grid: Grid, first: Cell, second: Cell) -> None:
    row, col = first
    target_row, target_col = second
    if row != target_row and col != target_col:
        raise ValueError("corridor segment must be axis-aligned")
    delta_row = (target_row > row) - (target_row < row)
    delta_col = (target_col > col) - (target_col < col)
    while True:
        grid[row][col] = 0
        if (row, col) == (target_row, target_col):
            return
        row += delta_row
        col += delta_col


def _build_base(
    height: int,
    width: int,
    n_intermediates: int,
    gaps: tuple[int, int, int],
) -> Grid:
    grid = full_grid(height, width, 8)
    # Keep every marker on a one-cell leaf spur. Removing the marker colors
    # therefore leaves the open-zero maze as one connected component, matching
    # the canonical visual grammar instead of fragmenting it at every waypoint.
    top, bottom = 2, height - 3
    columns = [1]
    for gap in gaps:
        columns.append(columns[-1] + gap)
    for row in (top, bottom):
        _carve_segment(grid, (row, columns[0]), (row, columns[-1]))
    rungs, order_nodes = _base_spec(n_intermediates)
    for column_index in rungs:
        _carve_segment(
            grid,
            (top, columns[column_index]),
            (bottom, columns[column_index]),
        )

    colors = [2, *range(4, 4 + n_intermediates), 3]
    for color, (rail, column_index) in zip(colors, order_nodes):
        row = top - 1 if rail == 0 else bottom + 1
        grid[row][columns[column_index]] = color
    return grid


def _orient(grid: Grid, orientation: str) -> Grid:
    if orientation == "identity":
        return [row[:] for row in grid]
    if orientation == "flip_h":
        return [list(reversed(row)) for row in grid]
    if orientation == "flip_v":
        return [row[:] for row in reversed(grid)]
    if orientation == "rot180":
        return [list(reversed(row)) for row in reversed(grid)]
    raise ValueError(f"unsupported orientation: {orientation!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic input grid for the selected Racket rule."""
    _validate_call(difficulty, overrides)
    dimension_or_count_override = any(
        overrides.get(axis) is not None
        for axis in ("grid_h", "grid_w", "n_intermediates")
    )
    canonical_anchor = not dimension_or_count_override and sample_index % 4 == 0
    profile = _CANONICAL_PROFILES[(int(seed) + int(sample_index) // 4) % 4]

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_int_axis(
        ctx, "grid_h", 9, 15, profile[0] if canonical_anchor else None
    )
    width = _draw_int_axis(
        ctx, "grid_w", 11, 19, profile[1] if canonical_anchor else None
    )
    n_intermediates = _draw_int_axis(
        ctx,
        "n_intermediates",
        2,
        3,
        profile[2] if canonical_anchor else None,
    )
    scheduled_orientation = ORIENTATIONS[int(sample_index) % len(ORIENTATIONS)]
    orientation = _draw_choice_axis(
        ctx,
        "orientation",
        ORIENTATIONS,
        None if overrides.get("orientation") is not None else scheduled_orientation,
    )

    gap_options = _valid_gap_splits(n_intermediates, height, width)
    if not gap_options:
        raise AssertionError(
            f"no lawful ladder split for {height}x{width}, {n_intermediates} checkpoints"
        )
    gaps = ctx.draw_rng("layout").choice(gap_options)
    grid = _orient(
        _build_base(height, width, n_intermediates, gaps),
        orientation,
    )
    errors = _generated_scene_errors(grid)
    if errors:
        raise AssertionError("generator constructed invalid grid: " + "; ".join(errors))
    observed = observe_overrides(grid)
    for axis, value in ctx.recorded_draws().items():
        if axis in AXES and observed.get(axis) != value:
            raise AssertionError(
                f"constructed {axis}={observed.get(axis)!r}, requested {value!r}"
            )
    return grid
