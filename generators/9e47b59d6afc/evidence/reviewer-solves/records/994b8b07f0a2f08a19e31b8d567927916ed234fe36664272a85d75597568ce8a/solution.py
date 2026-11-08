"""Visible-example solution for task 9e47b59d6afc."""


def _normalized_cells(grid, color):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    if not cells:
        raise ValueError(f"missing color {color}")
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return {(r - top, c - left) for r, c in cells}


def solve(grid):
    red = _normalized_cells(grid, 2)
    green = _normalized_cells(grid, 3)
    union = red | green
    height = max(r for r, _ in union) + 1
    width = max(c for _, c in union) + 1
    output = [[0 for _ in range(width)] for _ in range(height)]
    for r, c in union:
        if (r, c) in red and (r, c) in green:
            output[r][c] = 8
        elif (r, c) in red:
            output[r][c] = 2
        else:
            output[r][c] = 3
    return output
