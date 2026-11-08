"""Mark a shortest orthogonal path between the two colored maze endpoints."""

from collections import deque


def solve(grid):
    """Return the grid with path interiors recolored from 0 to 8."""
    result = [list(row) for row in grid]
    if not result or not result[0]:
        return result

    height, width = len(result), len(result[0])
    start = next(
        ((r, c) for r in range(height) for c in range(width)
         if result[r][c] == 2),
        None,
    )
    goal = next(
        ((r, c) for r in range(height) for c in range(width)
         if result[r][c] == 3),
        None,
    )
    if start is None or goal is None:
        return result

    predecessors = {start: None}
    queue = deque([start])
    while queue and goal not in predecessors:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
            neighbor = (r + dr, c + dc)
            nr, nc = neighbor
            if (0 <= nr < height and 0 <= nc < width
                    and result[nr][nc] in (0, 2, 3)
                    and neighbor not in predecessors):
                predecessors[neighbor] = (r, c)
                queue.append(neighbor)

    if goal in predecessors:
        cell = goal
        while cell is not None:
            r, c = cell
            if result[r][c] == 0:
                result[r][c] = 8
            cell = predecessors[cell]

    return result
