from collections import Counter


def solve(grid):
    """Toggle which of two perpendicular full-length stripes owns the overlap."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    if not height or not width:
        return out

    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    horizontal_rows = [
        r for r, row in enumerate(grid) if all(value != background for value in row)
    ]
    vertical_cols = [
        c
        for c in range(width)
        if all(grid[r][c] != background for r in range(height))
    ]
    if not horizontal_rows or not vertical_cols:
        return out

    horizontal_cells = [
        grid[r][c]
        for r in horizontal_rows
        for c in range(width)
        if c not in vertical_cols
    ]
    vertical_cells = [
        grid[r][c]
        for c in vertical_cols
        for r in range(height)
        if r not in horizontal_rows
    ]
    if not horizontal_cells or not vertical_cells:
        return out

    horizontal_color = Counter(horizontal_cells).most_common(1)[0][0]
    vertical_color = Counter(vertical_cells).most_common(1)[0][0]

    for r in horizontal_rows:
        for c in vertical_cols:
            if grid[r][c] == horizontal_color:
                out[r][c] = vertical_color
            elif grid[r][c] == vertical_color:
                out[r][c] = horizontal_color
    return out
