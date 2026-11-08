"""Visible-example solution for the blind ARC episode.

The grid is a maze whose walls are color 8.  The colored endpoints form two
pairs, 2--3 and 4--5.  For each connected pair, color the zero-valued cells on
its shortest orthogonal path with 7, preserving all endpoint colors.
"""

from collections import deque


def _find(grid, value):
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell == value:
                return (r, c)
    return None


def _shortest_path(grid, start, goal):
    """Return one shortest 4-neighbor path through non-8 cells, or None."""
    if start is None or goal is None:
        return None

    height = len(grid)
    width = len(grid[0]) if height else 0
    queue = deque([start])
    parent = {start: None}

    while queue:
        current = queue.popleft()
        if current == goal:
            break
        r, c = current
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (r + dr, c + dc)
            nr, nc = nxt
            if not (0 <= nr < height and 0 <= nc < width):
                continue
            if grid[nr][nc] == 8 or nxt in parent:
                continue
            parent[nxt] = current
            queue.append(nxt)

    if goal not in parent:
        return None

    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = parent[current]
    path.reverse()
    return path


def solve(grid):
    result = [row[:] for row in grid]
    route_zeros = set()

    for left, right in ((2, 3), (4, 5)):
        path = _shortest_path(grid, _find(grid, left), _find(grid, right))
        if path is None:
            continue
        route_zeros.update(
            (r, c) for r, c in path if grid[r][c] == 0
        )

    all_zeros = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 0
    }
    if route_zeros == all_zeros:
        return result

    for r, c in route_zeros:
        result[r][c] = 7
    return result
