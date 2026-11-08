"""Visible-example solution for the blind ARC task."""

from collections import deque


def _shortest_path(grid, start, goal, color):
    """Return one deterministic shortest 4-neighbor path avoiding color-8 walls."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    queue = deque([start])
    previous = {start: None}

    # This conventional order is consistent with every visible demonstration.
    for_current = ((-1, 0), (1, 0), (0, -1), (0, 1))

    while queue:
        row, col = queue.popleft()
        if (row, col) == goal:
            break
        for drow, dcol in for_current:
            nxt = (row + drow, col + dcol)
            nr, nc = nxt
            if not (0 <= nr < height and 0 <= nc < width):
                continue
            if nxt in previous or grid[nr][nc] == 8:
                continue
            # Do not route through a marker belonging to another pair.
            if grid[nr][nc] not in (0, color) and nxt != goal:
                continue
            previous[nxt] = (row, col)
            queue.append(nxt)

    if goal not in previous:
        return []

    path = []
    cursor = goal
    while cursor is not None:
        path.append(cursor)
        cursor = previous[cursor]
    path.reverse()
    return path


def solve(grid):
    """Connect each equal-colored marker pair by a shortest path through the maze."""
    if not grid:
        return []

    result = [row[:] for row in grid]
    locations = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value not in (0, 8):
                locations.setdefault(value, []).append((row, col))

    for color in sorted(locations):
        points = sorted(locations[color])
        if len(points) != 2:
            continue
        for row, col in _shortest_path(grid, points[0], points[1], color):
            if result[row][col] in (0, color):
                result[row][col] = color

    return result
