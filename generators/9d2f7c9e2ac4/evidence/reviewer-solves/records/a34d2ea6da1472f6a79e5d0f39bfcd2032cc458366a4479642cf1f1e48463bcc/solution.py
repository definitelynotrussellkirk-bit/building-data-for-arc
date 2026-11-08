"""Solve the visible quadrant analogy by rotating the lower-left object."""


def solve(grid):
    output = [list(row) for row in grid]
    if not grid or not grid[0]:
        return output
    height, width = len(grid), len(grid[0])
    divider_rows = [r for r in range(height) if all(value == 9 for value in grid[r])]
    divider_cols = [c for c in range(width) if all(grid[r][c] == 9 for r in range(height))]
    if len(divider_rows) != 1 or len(divider_cols) != 1:
        raise ValueError("Expected one full color-9 divider row and column")
    split_row, split_col = divider_rows[0], divider_cols[0]
    cells = [(r, c, grid[r][c])
             for r in range(split_row + 1, height)
             for c in range(split_col)
             if grid[r][c] not in (0, 9)]
    if not cells:
        return output

    top = min(r for r, _, _ in cells)
    left = min(c for _, c, _ in cells)
    bottom = max(r for r, _, _ in cells)
    object_height = bottom - top + 1
    row_offset = top - (split_row + 1)
    col_offset = left

    for r, c, color in cells:
        local_row, local_col = r - top, c - left
        target_row = split_row + 1 + row_offset + local_col
        target_col = split_col + 1 + col_offset + object_height - 1 - local_row
        if not (0 <= target_row < height and 0 <= target_col < width):
            raise ValueError("Rotated object does not fit the target quadrant")
        output[target_row][target_col] = color
    return output
