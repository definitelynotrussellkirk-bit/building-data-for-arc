"""Visible-example solution for the post-repair episode."""
from __future__ import annotations

from collections import deque
from copy import deepcopy

DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _distance_map(grid, start):
    height, width = len(grid), len(grid[0])
    distance = {start: 0}
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        for dr, dc in DIR4:
            nr, nc = row + dr, col + dc
            if (
                0 <= nr < height
                and 0 <= nc < width
                and grid[nr][nc] != 1
                and (nr, nc) not in distance
            ):
                distance[(nr, nc)] = distance[(row, col)] + 1
                queue.append((nr, nc))
    return distance


def solve(grid):
    if not grid or not grid[0]:
        return deepcopy(grid)
    seeds = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 1)
    ]
    maps = [
        (color, _distance_map(grid, (row, col)))
        for row, col, color in seeds
    ]
    output = deepcopy(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                continue
            candidates = [
                (distance[(row, col)], color)
                for color, distance in maps
                if (row, col) in distance
            ]
            if not candidates:
                continue
            best = min(distance for distance, _ in candidates)
            winners = {
                color for distance, color in candidates if distance == best
            }
            if len(winners) == 1:
                output[row][col] = next(iter(winners))
    return output
