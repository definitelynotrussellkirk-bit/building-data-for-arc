"""Fill the missing zero corner of each yellow 2-by-2 block."""


def solve(grid):
    """Return a copy with every 2x2 block of three 4s and one 0 completed in 9."""
    result = [list(row) for row in grid]
    if not grid:
        return result

    height, width = len(grid), len(grid[0])
    for row in range(height - 1):
        for column in range(width - 1):
            cells = (
                (row, column),
                (row, column + 1),
                (row + 1, column),
                (row + 1, column + 1),
            )
            if sum(grid[r][c] == 4 for r, c in cells) != 3:
                continue
            for r, c in cells:
                if grid[r][c] == 0:
                    result[r][c] = 9
    return result
