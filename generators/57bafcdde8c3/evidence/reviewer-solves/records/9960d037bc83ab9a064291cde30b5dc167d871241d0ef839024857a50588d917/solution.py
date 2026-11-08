"""Visible-example solution: highlight non-singleton foreground groups."""

from collections import Counter


def solve(grid):
    """Recolor foreground cells with a same-color cardinal neighbor to 8."""
    result = [list(row) for row in grid]
    if not grid or not grid[0]:
        return result

    height, width = len(grid), len(grid[0])
    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]

    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == background:
                continue
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = row + dr, column + dc
                if (0 <= nr < height and 0 <= nc < width
                        and grid[nr][nc] == color):
                    result[row][column] = 8
                    break

    return result
