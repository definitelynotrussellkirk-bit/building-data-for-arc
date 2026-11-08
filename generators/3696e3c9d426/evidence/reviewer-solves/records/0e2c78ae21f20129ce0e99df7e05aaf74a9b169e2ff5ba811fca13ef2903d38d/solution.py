"""Blind solution inferred only from solve-blind/challenge.json."""


def solve(grid):
    """Apply independent downward gravity to every column.

    Nonzero cells keep their top-to-bottom order and are packed against the
    bottom edge of their original column. Zero is the background.
    """
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    out = [[0 for _ in range(width)] for _ in range(height)]
    for col in range(width):
        values = [grid[row][col] for row in range(height) if grid[row][col] != 0]
        start = height - len(values)
        for offset, value in enumerate(values):
            out[start + offset][col] = value
    return out
