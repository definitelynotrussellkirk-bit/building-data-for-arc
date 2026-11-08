from __future__ import annotations


def solve(grid):
    """Align every nonzero color's top row to color 1's original top row."""
    if not isinstance(grid, list) or not grid or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    height = len(grid)
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    cells_by_color = {}
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value != 0:
                cells_by_color.setdefault(value, []).append((row_index, col_index))

    if 1 not in cells_by_color:
        raise ValueError("color 1 is required as the vertical anchor")

    blue_top = min(row for row, _ in cells_by_color[1])
    output = [[0 for _ in range(width)] for _ in range(height)]
    for color, cells in cells_by_color.items():
        color_top = min(row for row, _ in cells)
        shift = blue_top - color_top
        for row, col in cells:
            new_row = row + shift
            if not 0 <= new_row < height:
                raise ValueError("alignment would move a cell outside the grid")
            if output[new_row][col] != 0:
                raise ValueError("alignment would collide with another color")
            output[new_row][col] = color
    return output
