from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Mark crossings of unblocked rays from the top and left headers.

    A 2 in the top row emits a downward ray, and a 1 in the first column
    emits a rightward ray.  Color 5 blocks a ray.  Body cells reached by both
    rays become 6; all other cells are 0.
    """
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    out = [[0 for _ in range(width)] for _ in range(height)]

    top_columns = [c for c in range(1, width) if grid[0][c] == 2]
    left_rows = [r for r in range(1, height) if grid[r][0] == 1]

    for r in left_rows:
        for c in top_columns:
            horizontal_clear = all(grid[r][x] != 5 for x in range(1, c + 1))
            vertical_clear = all(grid[y][c] != 5 for y in range(1, r + 1))
            if horizontal_clear and vertical_clear:
                out[r][c] = 6

    return out
