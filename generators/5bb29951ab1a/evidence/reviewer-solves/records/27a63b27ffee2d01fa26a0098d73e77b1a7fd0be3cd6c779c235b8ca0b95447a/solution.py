"""Visible-example solution for task 5bb29951ab1a."""
from collections import Counter


def solve(grid):
    """Absorb a sparse-color cell iff it has >=2 orthogonal modal-color neighbors."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    counts = Counter(value for row in grid for value in row if value != 0)
    if len(counts) != 2:
        return [list(row) for row in grid]
    rectangle_color, dot_color = (color for color, _ in counts.most_common())

    height, width = len(grid), len(grid[0])
    out = [list(row) for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != dot_color:
                continue
            adjacent = sum(
                0 <= row + dr < height
                and 0 <= col + dc < width
                and grid[row + dr][col + dc] == rectangle_color
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            )
            out[row][col] = rectangle_color if adjacent >= 2 else 0
    return out
