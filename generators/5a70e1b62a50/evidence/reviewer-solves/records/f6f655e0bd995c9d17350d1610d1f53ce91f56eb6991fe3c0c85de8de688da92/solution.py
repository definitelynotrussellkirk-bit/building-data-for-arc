"""Visible-example solution for task 5a70e1b62a50."""
from __future__ import annotations

from collections import deque


def solve(grid):
    """Fill each zero region cut off from the border by one surrounding color."""
    out = [list(row) for row in grid]
    height = len(grid)
    width = len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 0
    }
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    while unseen:
        start = unseen.pop()
        queue = deque([start])
        region = {start}
        touches_border = False
        neighboring_colors = set()

        while queue:
            row, col = queue.popleft()
            if row in (0, height - 1) or col in (0, width - 1):
                touches_border = True
            for d_row, d_col in directions:
                next_row = row + d_row
                next_col = col + d_col
                if not (0 <= next_row < height and 0 <= next_col < width):
                    continue
                value = grid[next_row][next_col]
                point = (next_row, next_col)
                if value == 0 and point in unseen:
                    unseen.remove(point)
                    region.add(point)
                    queue.append(point)
                elif value != 0:
                    neighboring_colors.add(value)

        if not touches_border and len(neighboring_colors) == 1:
            fill = next(iter(neighboring_colors))
            for row, col in region:
                out[row][col] = fill

    return out
