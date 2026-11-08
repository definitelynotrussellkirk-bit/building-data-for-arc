from __future__ import annotations

from collections import deque


def solve(grid):
    """Recolor endpoints only when the whole red component is a straight line."""
    out = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    }

    while unseen:
        start = next(iter(unseen))
        unseen.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = row + drow, col + dcol
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)

        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        if min(rows) == max(rows):
            row = rows[0]
            out[row][min(cols)] = 4
            out[row][max(cols)] = 4
        elif min(cols) == max(cols):
            col = cols[0]
            out[min(rows)][col] = 4
            out[max(rows)][col] = 4

    return out
