"""Visible-example solution for ARC task f8d1d470d522."""

from __future__ import annotations

import heapq


_DIRECTIONS = ((-1, 0), (0, -1), (0, 1), (1, 0))


def _neighbors(row: int, col: int, height: int, width: int):
    for direction, (dr, dc) in enumerate(_DIRECTIONS):
        nr, nc = row + dr, col + dc
        if 0 <= nr < height and 0 <= nc < width:
            yield direction, nr, nc


def solve(grid):
    """Paint the shortest legal 8/9 route between the two 9 markers with 9.

    Color-8 cells sharing an edge with a color-7 obstacle are unavailable.
    Among equal-length routes, prefer the route with the fewest direction
    changes.  A coordinate-path key makes any remaining tie deterministic.
    """
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        raise ValueError("grid must be a non-empty rectangular list")
    height, width = len(grid), len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    endpoints = sorted(
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 9
    )
    if len(endpoints) != 2:
        raise ValueError("expected exactly two color-9 markers")
    start, goal = endpoints

    obstacles = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 7
    }
    disabled = set()
    for row, col in obstacles:
        for _direction, nr, nc in _neighbors(row, col, height, width):
            if grid[nr][nc] == 8:
                disabled.add((nr, nc))

    def walkable(position):
        row, col = position
        return grid[row][col] in (8, 9) and position not in disabled

    # Heap order is the complete preference order inferred from the examples:
    # shortest route, then fewest turns, then a stable coordinate-path tie.
    initial_path = (start,)
    heap = [(0, 0, initial_path, start[0], start[1], -1)]
    best = {(start[0], start[1], -1): (0, 0, initial_path)}
    chosen_path = None

    while heap:
        steps, turns, path, row, col, previous_direction = heapq.heappop(heap)
        state = (row, col, previous_direction)
        if best.get(state) != (steps, turns, path):
            continue
        if (row, col) == goal:
            chosen_path = path
            break

        for direction, nr, nc in _neighbors(row, col, height, width):
            position = (nr, nc)
            if not walkable(position):
                continue
            next_steps = steps + 1
            next_turns = turns + int(
                previous_direction != -1 and direction != previous_direction
            )
            next_path = path + (position,)
            next_state = (nr, nc, direction)
            score = (next_steps, next_turns, next_path)
            if score < best.get(next_state, (10**9, 10**9, ())):
                best[next_state] = score
                heapq.heappush(
                    heap,
                    (next_steps, next_turns, next_path, nr, nc, direction),
                )

    if chosen_path is None:
        raise ValueError("no legal route joins the two markers")

    output = [row[:] for row in grid]
    for row, col in chosen_path:
        output[row][col] = 9
    return output
