"""Solve the visible shape-comparison hypothesis inferred from the examples."""


def _normalized_cells(grid, color):
    cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    if not cells:
        return set()
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return {(row - min_row, col - min_col) for row, col in cells}


def solve(input_grid):
    red = _normalized_cells(input_grid, 2)
    green = _normalized_cells(input_grid, 3)
    overlap_mode = any(7 in row for row in input_grid)
    selected = red & green if overlap_mode else red ^ green
    if not selected:
        return [[0]]

    top = min(row for row, _ in selected)
    bottom = max(row for row, _ in selected)
    left = min(col for _, col in selected)
    right = max(col for _, col in selected)
    output = [[0] * (right - left + 1) for _ in range(bottom - top + 1)]
    for row, col in selected:
        output[row - top][col - left] = 8
    return output
