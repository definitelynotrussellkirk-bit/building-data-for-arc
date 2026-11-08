def solve(grid):
    """Mirror the grid's 2-column macro-cells while preserving each cell."""
    if not grid:
        return []
    width = len(grid[0])
    if width % 2:
        raise ValueError("expected an even-width grid of 2-column macro-cells")
    if any(len(row) != width for row in grid):
        raise ValueError("ragged grid")

    result = []
    for row in grid:
        cells = [row[col : col + 2] for col in range(0, width, 2)]
        result.append([value for cell in reversed(cells) for value in cell])
    return result
