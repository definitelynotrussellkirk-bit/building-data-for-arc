"""Visible-example solution for the post-repair solve episode."""
from __future__ import annotations

from collections import deque
from copy import deepcopy


def solve(grid):
    """Flood each 4-connected non-wall room with its unique seed color."""
    if not grid or not grid[0]:
        return deepcopy(grid)
    height = len(grid)
    width = len(grid[0])
    output = deepcopy(grid)
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 1
    }
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        room = {start}
        while queue:
            row, col = queue.popleft()
            for point in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if point in unseen:
                    unseen.remove(point)
                    room.add(point)
                    queue.append(point)
        colors = {
            grid[row][col]
            for row, col in room
            if grid[row][col] != 0
        }
        if len(colors) == 1:
            color = next(iter(colors))
            for row, col in room:
                if output[row][col] == 0:
                    output[row][col] = color
    return output
