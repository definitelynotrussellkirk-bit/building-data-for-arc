def solve(grid):
    """Summarize the horizontal/vertical separators in a two-color grid."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("Expected a nonempty rectangular grid")
    colors = {value for row in grid for value in row}
    if len(colors) != 2:
        raise ValueError("Expected two colors")
    height, width = len(grid), len(grid[0])
    counts = {}
    for color in colors:
        rows = sum(all(value == color for value in row) for row in grid)
        columns = sum(all(grid[r][c] == color for r in range(height))
                      for c in range(width))
        counts[color] = (rows, columns)
    separator = max(colors, key=lambda color: sum(counts[color]))
    background = next(color for color in colors if color != separator)
    rows, columns = counts[separator]
    return [[background] * (columns + 1) for _ in range(rows + 1)]
