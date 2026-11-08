"""Visible-example solution for 3ef9eae12446."""


def solve(grid):
    if not grid or not grid[0]:
        return [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    out = [list(row) for row in grid]
    border_offsets = (
        (0, 0), (0, 1), (0, 2),
        (1, 0),         (1, 2),
        (2, 0), (2, 1), (2, 2),
    )
    for row0 in range(height - 2):
        for col0 in range(width - 2):
            center_row, center_col = row0 + 1, col0 + 1
            color = grid[row0][col0]
            if color == 0 or grid[center_row][center_col] != 0:
                continue
            if all(grid[row0 + dr][col0 + dc] == color for dr, dc in border_offsets):
                out[center_row][center_col] = color
    return out
