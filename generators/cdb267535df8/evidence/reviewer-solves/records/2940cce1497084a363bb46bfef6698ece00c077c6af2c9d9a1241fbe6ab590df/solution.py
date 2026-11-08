"""Solve the visible challenge using shortest paths around gray barriers."""

from collections import deque


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [list(row) for row in grid]
    seeds = {}
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color not in (0, 5):
                seeds.setdefault(color, []).append((row, col))

    distances = {}
    for color, starts in seeds.items():
        distance = [[None] * width for _ in range(height)]
        queue = deque(starts)
        for row, col in starts:
            distance[row][col] = 0
        while queue:
            row, col = queue.popleft()
            for next_row, next_col in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if (
                    0 <= next_row < height
                    and 0 <= next_col < width
                    and grid[next_row][next_col] != 5
                    and distance[next_row][next_col] is None
                ):
                    distance[next_row][next_col] = distance[row][col] + 1
                    queue.append((next_row, next_col))
        distances[color] = distance

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0:
                continue
            candidates = [
                (distance[row][col], color)
                for color, distance in distances.items()
                if distance[row][col] is not None
            ]
            if not candidates:
                continue
            minimum = min(distance for distance, _ in candidates)
            winners = [color for distance, color in candidates if distance == minimum]
            if len(winners) == 1:
                result[row][col] = winners[0]
    return result
