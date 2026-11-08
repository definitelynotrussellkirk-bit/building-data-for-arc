"""Visible-example solution for task 12a886996b14."""


def solve(grid):
    """Move every yellow cell by the red-marker to green-marker displacement."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    red = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    green = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]
    yellow = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 4]
    if not red or not green:
        return [[0 for _ in range(width)] for _ in range(height)]

    red_anchor = (min(r for r, _ in red), min(c for _, c in red))
    green_anchor = (min(r for r, _ in green), min(c for _, c in green))
    dr = green_anchor[0] - red_anchor[0]
    dc = green_anchor[1] - red_anchor[1]

    out = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in yellow:
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < height and 0 <= new_col < width:
            out[new_row][new_col] = 4
    return out
