def solve(grid):
    """Complete each header color's vertical-and-side connector."""
    h = len(grid)
    w = len(grid[0])
    header = [(col, color) for col, color in enumerate(grid[0]) if color != 0]
    dots = [
        (row, col, grid[row][col])
        for row in range(1, h)
        for col in range(w)
        if grid[row][col] != 0
    ]

    entries = []
    for header_col, color in header:
        dot = next((item for item in dots if item[2] == color), None)
        if dot is None:
            entries.append((header_col, color, h - 1, None))
        else:
            entries.append((header_col, color, dot[0], dot[1]))

    out = [[0 for _ in range(w)] for _ in range(h)]
    for row in range(h):
        for col in range(w):
            for header_col, color, target_row, target_col in entries:
                vertical = col == header_col and row <= target_row
                horizontal = (
                    target_col is not None
                    and row == target_row
                    and min(header_col, target_col) <= col <= max(header_col, target_col)
                )
                if vertical or horizontal:
                    out[row][col] = color
                    break
    return out
