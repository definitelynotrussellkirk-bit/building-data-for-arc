"""Visible-example solution: reflect a template and stamp at the marker."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    template = [(row, col) for row in range(height) for col in range(width)
                if grid[row][col] == 2]
    markers = [(row, col) for row in range(height) for col in range(width)
               if grid[row][col] == 1]
    if not template or len(markers) != 1:
        raise ValueError("expected a red template and one blue marker")
    top = min(row for row, _ in template)
    right = max(col for _, col in template)
    anchor_row, anchor_col = markers[0]
    result = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in template:
        target_row = anchor_row + row - top
        target_col = anchor_col + right - col
        if 0 <= target_row < height and 0 <= target_col < width:
            result[target_row][target_col] = 8
    return result
