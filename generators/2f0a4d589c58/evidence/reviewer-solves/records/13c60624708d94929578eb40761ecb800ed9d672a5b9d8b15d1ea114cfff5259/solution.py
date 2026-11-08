from collections import Counter


def _mode(values):
    return Counter(values).most_common(1)[0][0]


def solve(grid):
    """Toggle which complete colored line is visible at every crossing."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    background = _mode(cell for row in grid for cell in row)

    full_rows = [
        r for r in range(height)
        if all(grid[r][c] != background for c in range(width))
    ]
    full_cols = [
        c for c in range(width)
        if all(grid[r][c] != background for r in range(height))
    ]

    row_colors = {}
    for r in full_rows:
        non_crossings = [grid[r][c] for c in range(width) if c not in full_cols]
        row_colors[r] = _mode(non_crossings or grid[r])

    col_colors = {}
    for c in full_cols:
        non_crossings = [grid[r][c] for r in range(height) if r not in full_rows]
        column = [grid[r][c] for r in range(height)]
        col_colors[c] = _mode(non_crossings or column)

    result = [row[:] for row in grid]
    for r in full_rows:
        for c in full_cols:
            row_color = row_colors[r]
            col_color = col_colors[c]
            if row_color == col_color:
                continue
            if grid[r][c] == row_color:
                result[r][c] = col_color
            elif grid[r][c] == col_color:
                result[r][c] = row_color

    return result
