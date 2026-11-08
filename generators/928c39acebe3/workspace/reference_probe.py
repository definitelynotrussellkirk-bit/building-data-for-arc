"""Independent ray-trace oracle and shortcut probes for task 928c39acebe3.

This module deliberately does not import the production generator.  It gives
future reviewers a small executable reference for canonical parity, incoming
mirror-direction coverage, and the two strongest source-bound shortcuts.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Sequence

TASK_ID = "928c39acebe3"
OFFICIAL_TURNS = {
    (4, 0, 1): (-1, 0),
    (4, -1, 0): (0, 1),
    (4, 0, -1): (1, 0),
    (4, 1, 0): (0, -1),
    (5, 0, 1): (1, 0),
    (5, 1, 0): (0, 1),
    (5, 0, -1): (-1, 0),
    (5, -1, 0): (0, -1),
}
DIRECTION_NAMES = {(0, 1): "east", (1, 0): "south", (0, -1): "west", (-1, 0): "north"}


def _shape(grid: Sequence[Sequence[int]]) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be non-empty")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("rows must be non-empty")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    return len(grid), width


def trace_details(
    grid: Sequence[Sequence[int]],
    *,
    slash_west_mode: str = "official",
    backslash_north_mode: str = "official",
    mirror_mode: str = "official",
    ignore_blocker: bool = False,
    stop_after_mirrors: int | None = None,
    paint_mirrors: bool = True,
) -> dict[str, Any]:
    """Trace every color-2 emitter exactly as the selected rule variant does."""
    height, width = _shape(grid)
    output = [[0 for _ in range(width)] for _ in range(height)]
    all_paths: list[tuple[int, int]] = []
    hits: list[tuple[int, int, int, int, int]] = []
    stops: list[dict[str, Any]] = []
    looped = False
    emitters = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    ]
    for source_row, source_col in emitters:
        row, col = source_row, source_col
        dr, dc = 0, 1
        seen: set[tuple[int, int, int, int]] = set()
        mirror_count = 0
        while True:
            next_row, next_col = row + dr, col + dc
            if not (0 <= next_row < height and 0 <= next_col < width):
                stops.append({"kind": "edge", "at": (next_row, next_col), "direction": (dr, dc)})
                break
            state = (next_row, next_col, dr, dc)
            if state in seen:
                looped = True
                stops.append({"kind": "loop", "at": (next_row, next_col), "direction": (dr, dc)})
                break
            seen.add(state)
            value = grid[next_row][next_col]
            if value == 2:
                stops.append({"kind": "emitter", "at": (next_row, next_col), "direction": (dr, dc)})
                break
            if value == 6 and not ignore_blocker:
                stops.append({"kind": "blocker", "at": (next_row, next_col), "direction": (dr, dc)})
                break

            all_paths.append((next_row, next_col))
            if value != 6 and (paint_mirrors or value == 0):
                output[next_row][next_col] = 8
            elif value == 6 and ignore_blocker:
                output[next_row][next_col] = 8

            if value in (4, 5):
                incoming = (dr, dc)
                hits.append((next_row, next_col, value, dr, dc))
                mirror_count += 1
                if stop_after_mirrors is not None and mirror_count >= stop_after_mirrors:
                    stops.append({"kind": "mirror_limit", "at": (next_row, next_col), "direction": incoming})
                    break
                if mirror_mode == "swapped":
                    value = 5 if value == 4 else 4
                elif mirror_mode == "straight":
                    value = 0
                elif mirror_mode == "stop":
                    stops.append({"kind": "mirror", "at": (next_row, next_col), "direction": incoming})
                    break
                if value in (4, 5):
                    if value == 4 and incoming == (0, -1) and slash_west_mode == "straight":
                        pass
                    elif value == 5 and incoming == (-1, 0) and backslash_north_mode == "straight":
                        pass
                    else:
                        dr, dc = OFFICIAL_TURNS[(value, dr, dc)]
            row, col = next_row, next_col

    return {
        "output": output,
        "emitters": emitters,
        "path": all_paths,
        "hits": hits,
        "hit_colors": tuple(hit[2] for hit in hits),
        "incoming": tuple((hit[2], DIRECTION_NAMES[(hit[3], hit[4])]) for hit in hits),
        "stops": stops,
        "looped": looped,
    }


def official_output(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return trace_details(grid)["output"]


def slash_from_west_continues(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: a slash approached from west fails to turn."""
    return trace_details(grid, slash_west_mode="straight")["output"]


def backslash_from_north_continues(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: a backslash approached from north fails to turn."""
    return trace_details(grid, backslash_north_mode="straight")["output"]


def profile(grid: Sequence[Sequence[int]]) -> tuple[int, int, tuple[int, ...]]:
    details = trace_details(grid)
    height, width = _shape(grid)
    return height, width, details["hit_colors"]


def incoming_pairs(grid: Sequence[Sequence[int]]) -> set[tuple[int, str]]:
    return set(trace_details(grid)["incoming"])


def differs_at(
    left: Sequence[Sequence[int]], right: Sequence[Sequence[int]]
) -> list[tuple[int, int, int, int]]:
    """Return exact cellwise disagreements as (row, col, left, right)."""
    _shape(left)
    _shape(right)
    return [
        (row, col, left[row][col], right[row][col])
        for row in range(len(left))
        for col in range(len(left[0]))
        if left[row][col] != right[row][col]
    ]


def assert_input_pure(function, grid: Sequence[Sequence[int]]) -> list[list[int]]:
    before = deepcopy(grid)
    result = function(grid)
    if grid != before:
        raise AssertionError(f"{function.__name__} mutated its input")
    return result
