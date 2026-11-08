from __future__ import annotations

from collections import Counter


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Extract the palette and apply the large block-pattern as its mask."""
    if not grid or not grid[0]:
        return []

    counts = Counter(value for row in grid for value in row if value != 0)
    if not counts:
        return []
    shape_color = max(counts, key=counts.get)

    shape_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == shape_color
    ]
    other_colored_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0 and value != shape_color
    ]
    if not other_colored_cells:
        return []

    shape_top = min(row for row, _ in shape_cells)
    shape_left = min(col for _, col in shape_cells)
    shape_bottom = max(row for row, _ in shape_cells)
    shape_right = max(col for _, col in shape_cells)

    palette_top = min(row for row, _ in other_colored_cells)
    palette_left = min(col for _, col in other_colored_cells)
    palette_bottom = max(row for row, _ in other_colored_cells)
    palette_right = max(col for _, col in other_colored_cells)

    palette_height = palette_bottom - palette_top + 1
    palette_width = palette_right - palette_left + 1
    block_height = (shape_bottom - shape_top + 1) // palette_height
    block_width = (shape_right - shape_left + 1) // palette_width

    output: list[list[int]] = []
    for block_row in range(palette_height):
        row: list[int] = []
        for block_col in range(palette_width):
            sample_row = shape_top + block_row * block_height
            sample_col = shape_left + block_col * block_width
            palette_value = grid[palette_top + block_row][palette_left + block_col]
            row.append(
                palette_value
                if grid[sample_row][sample_col] == shape_color
                else 0
            )
        output.append(row)
    return output
