from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Paint intersections of unblocked top-down and left-right rays."""
    if not grid or not grid[0]:
        return []
    height = len(grid)
    width = len(grid[0])

    vertical_reach: set[tuple[int, int]] = set()
    for col in range(1, width):
        if grid[0][col] != 2:
            continue
        for row in range(1, height):
            if grid[row][col] == 5:
                break
            vertical_reach.add((row, col))

    horizontal_reach: set[tuple[int, int]] = set()
    for row in range(1, height):
        if grid[row][0] != 1:
            continue
        for col in range(1, width):
            if grid[row][col] == 5:
                break
            horizontal_reach.add((row, col))

    output = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in vertical_reach & horizontal_reach:
        output[row][col] = 6
    return output
