"""Visible-example solution for the exposed post-repair episode."""
from __future__ import annotations

from collections import deque


def solve(grid):
    """Encode each nonzero 4-connected object as a sorted color run."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    objects = []

    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            start = (start_row, start_col)
            if color == 0 or start in seen:
                continue
            queue = deque([start])
            seen.add(start)
            size = 0
            while queue:
                row, col = queue.popleft()
                size += 1
                for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                    nxt = (row + dr, col + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            objects.append((size, color))

    objects.sort(key=lambda item: (-item[0], item[1]))
    output = []
    for index, (size, color) in enumerate(objects):
        if index:
            output.append(0)
        output.extend([color] * size)
    return [output]
