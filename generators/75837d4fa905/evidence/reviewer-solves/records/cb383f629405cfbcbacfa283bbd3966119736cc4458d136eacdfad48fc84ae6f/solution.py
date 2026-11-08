from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Bloom every solid nonzero 2x2 square at its four diagonal corners."""
    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]

    # Detect source squares from the original input.  Apply them in row-major
    # order, writing only onto cells that are still background.
    for row in range(height - 1):
        for col in range(width - 1):
            colour = grid[row][col]
            if colour == 0:
                continue
            if not (
                grid[row][col + 1] == colour
                and grid[row + 1][col] == colour
                and grid[row + 1][col + 1] == colour
            ):
                continue
            for dr, dc in ((-1, -1), (-1, 2), (2, -1), (2, 2)):
                rr, cc = row + dr, col + dc
                if 0 <= rr < height and 0 <= cc < width and output[rr][cc] == 0:
                    output[rr][cc] = colour
    return output
