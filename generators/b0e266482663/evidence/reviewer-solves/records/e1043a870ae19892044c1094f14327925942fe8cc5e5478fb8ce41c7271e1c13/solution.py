from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Extend edge markers as rays until a gray blocker.

    Red (2) markers in the first column emit horizontal rays to the right.
    Green (3) markers in the first row emit vertical rays downward. Gray (9)
    cells block either ray and remain unchanged. A blank cell reached by both
    rays becomes azure (8); cells reached by one ray take that ray's color.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    horizontal = [[False] * width for _ in range(height)]
    vertical = [[False] * width for _ in range(height)]

    for row in range(height):
        if grid[row][0] != 2:
            continue
        for col in range(width):
            if grid[row][col] == 9:
                break
            horizontal[row][col] = True

    for col in range(width):
        if grid[0][col] != 3:
            continue
        for row in range(height):
            if grid[row][col] == 9:
                break
            vertical[row][col] = True

    result = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0:
                continue
            if horizontal[row][col] and vertical[row][col]:
                result[row][col] = 8
            elif horizontal[row][col]:
                result[row][col] = 2
            elif vertical[row][col]:
                result[row][col] = 3

    return result
