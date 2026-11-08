from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Replace every orthogonally touching 2/3 pair by 0/8 respectively."""
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    participating: set[tuple[int, int]] = set()
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value not in (2, 3):
                continue
            opposite = 3 if value == 2 else 2
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nrow, ncol = row + drow, col + dcol
                if (
                    0 <= nrow < height
                    and 0 <= ncol < width
                    and grid[nrow][ncol] == opposite
                ):
                    participating.add((row, col))
                    participating.add((nrow, ncol))

    result = [row[:] for row in grid]
    for row, col in participating:
        result[row][col] = 0 if grid[row][col] == 2 else 8
    return result
