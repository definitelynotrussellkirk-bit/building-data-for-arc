"""Solve the transformation inferred from the visible challenge examples."""

from collections import Counter


def solve(grid):
    """Swap object colors and shift its upper half by its left margin."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    height, width = len(grid), len(grid[0])
    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    cells = [
        (row, col, color)
        for row, values in enumerate(grid)
        for col, color in enumerate(values)
        if color != background
    ]
    if not cells:
        return [list(row) for row in grid]

    colors = sorted({color for _, _, color in cells})
    if len(colors) != 2:
        raise ValueError("Expected an object using exactly two foreground colors")
    exchange = {colors[0]: colors[1], colors[1]: colors[0]}
    top = min(row for row, _, _ in cells)
    bottom = max(row for row, _, _ in cells)
    left = min(col for _, col, _ in cells)
    middle = (top + bottom + 1) // 2

    result = [[background] * width for _ in range(height)]
    for row, col, color in cells:
        destination = col + left if row < middle else col
        if 0 <= destination < width:
            result[row][destination] = exchange[color]
    return result
