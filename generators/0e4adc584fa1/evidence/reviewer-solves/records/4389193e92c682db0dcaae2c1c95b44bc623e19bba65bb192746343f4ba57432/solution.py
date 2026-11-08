"""Visible-only solution for task 0e4adc584fa1."""


def _rotate_clockwise(grid):
    return [list(row) for row in zip(*grid[::-1])]


def solve(grid):
    """Crop the colored figure and rotate it by the isolated 1..4 marker."""
    marker = None
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if 1 <= value <= 4:
                marker = (r, c, value)
                break
        if marker is not None:
            break
    if marker is None:
        raise ValueError("expected one isolated rotation marker with color 1..4")

    marker_r, marker_c, turns_code = marker
    figure_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and (r, c) != (marker_r, marker_c)
    ]
    if not figure_cells:
        raise ValueError("expected a non-marker colored figure")

    top = min(r for r, _ in figure_cells)
    bottom = max(r for r, _ in figure_cells)
    left = min(c for _, c in figure_cells)
    right = max(c for _, c in figure_cells)
    cropped = [row[left:right + 1] for row in grid[top:bottom + 1]]

    result = cropped
    for _ in range(turns_code - 1):
        result = _rotate_clockwise(result)
    return result
