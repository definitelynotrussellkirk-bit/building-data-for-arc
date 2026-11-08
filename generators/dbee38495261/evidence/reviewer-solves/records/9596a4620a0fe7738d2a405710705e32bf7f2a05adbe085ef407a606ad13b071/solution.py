"""Visible-example solve for ordered waypoint routing in a wall maze."""
from collections import deque


def solve(grid):
    h, w = len(grid), len(grid[0])
    positions = {
        value: (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if 2 <= value <= 7
    }
    mids = sorted(value for value in positions if value not in (2, 3))
    order = [2, *mids, 3]
    output = [row[:] for row in grid]
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    for first, second in zip(order, order[1:]):
        start, goal = positions[first], positions[second]
        queue = deque([start])
        previous = {start: None}
        while queue:
            cell = queue.popleft()
            if cell == goal:
                break
            for dr, dc in directions:
                nxt = (cell[0] + dr, cell[1] + dc)
                if not (0 <= nxt[0] < h and 0 <= nxt[1] < w):
                    continue
                if nxt in previous or grid[nxt[0]][nxt[1]] == 1:
                    continue
                previous[nxt] = cell
                queue.append(nxt)
        if goal not in previous:
            raise ValueError(f"no route between marker {first} and {second}")
        path = []
        cursor = goal
        while cursor is not None:
            path.append(cursor)
            cursor = previous[cursor]
        for row, col in reversed(path[1:-1]):
            if output[row][col] == 0:
                output[row][col] = 8
    return output
