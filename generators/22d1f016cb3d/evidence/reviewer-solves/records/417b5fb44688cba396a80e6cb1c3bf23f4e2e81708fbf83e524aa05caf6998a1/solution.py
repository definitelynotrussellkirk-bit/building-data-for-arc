from __future__ import annotations


def solve(grid):
    """Recolor each 5 from the two opposing cardinal-neighbor tests."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [list(row) for row in grid]

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 5:
                continue

            horizontal_pair = (
                col > 0
                and col + 1 < width
                and grid[row][col - 1] == 5
                and grid[row][col + 1] == 5
            )
            vertical_pair = (
                row > 0
                and row + 1 < height
                and grid[row - 1][col] == 5
                and grid[row + 1][col] == 5
            )

            if horizontal_pair and vertical_pair:
                output[row][col] = 2
            elif not horizontal_pair and not vertical_pair:
                output[row][col] = 1
            else:
                output[row][col] = 4

    return output
