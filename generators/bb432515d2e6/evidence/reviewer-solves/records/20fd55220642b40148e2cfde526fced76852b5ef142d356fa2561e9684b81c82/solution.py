from __future__ import annotations

from collections import deque
from typing import Sequence


def solve(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Assign each zero to its unique nearest seed color through non-5 cells."""
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be non-empty and rectangular")

    colors = sorted({value for row in grid for value in row if value not in (0, 5)})
    unreachable = height * width + 1
    distance_by_color: dict[int, list[list[int]]] = {}

    for color in colors:
        distance = [[unreachable] * width for _ in range(height)]
        queue: deque[tuple[int, int]] = deque()
        for row in range(height):
            for col in range(width):
                if grid[row][col] == color:
                    distance[row][col] = 0
                    queue.append((row, col))
        while queue:
            row, col = queue.popleft()
            candidate = distance[row][col] + 1
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                next_row, next_col = row + drow, col + dcol
                if (
                    0 <= next_row < height
                    and 0 <= next_col < width
                    and grid[next_row][next_col] != 5
                    and candidate < distance[next_row][next_col]
                ):
                    distance[next_row][next_col] = candidate
                    queue.append((next_row, next_col))
        distance_by_color[color] = distance

    output = [list(row) for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0:
                continue
            best = min(
                (distance_by_color[color][row][col] for color in colors),
                default=unreachable,
            )
            winners = [
                color
                for color in colors
                if distance_by_color[color][row][col] == best
            ]
            if best < unreachable and len(winners) == 1:
                output[row][col] = winners[0]
    return output
