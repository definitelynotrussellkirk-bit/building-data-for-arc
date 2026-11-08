"""Standalone solution inferred and checked against this episode's visible pairs.

No repository imports, file reads, stored answers, or source-rule calls.
"""
from collections import deque


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected a nonempty rectangular grid')
    height, width = len(grid), len(grid[0])
    result = [[0] * width for _ in range(height)]
    visited: set[tuple[int, int]] = set()
    for row in range(height):
        for column in range(width):
            shade = grid[row][column]
            if shade == 0 or (row, column) in visited:
                continue
            frontier = deque([(row, column)])
            visited.add((row, column))
            count = 0
            top = bottom = row
            left = right = column
            while frontier:
                y, x = frontier.popleft()
                count += 1
                top, bottom = min(top, y), max(bottom, y)
                left, right = min(left, x), max(right, x)
                for a, b in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if (0 <= a < height and 0 <= b < width
                            and (a, b) not in visited and grid[a][b] == shade):
                        visited.add((a, b))
                        frontier.append((a, b))
            if count == (bottom - top + 1) * (right - left + 1):
                for y in (top, bottom):
                    for x in (left, right):
                        result[y][x] = shade
    return result
