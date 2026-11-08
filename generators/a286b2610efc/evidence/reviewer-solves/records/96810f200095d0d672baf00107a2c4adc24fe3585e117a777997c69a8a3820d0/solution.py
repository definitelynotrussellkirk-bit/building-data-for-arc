from collections import defaultdict


def solve(grid):
    """Extend every nonzero two-cell bar by one cell at each end, clipped."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    by_color = defaultdict(list)
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                by_color[color].append((row_index, column_index))

    for color, cells in by_color.items():
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = sorted(cells)
        dr = r2 - r1
        dc = c2 - c1
        if abs(dr) + abs(dc) != 1:
            continue
        for row_index, column_index in ((r1 - dr, c1 - dc), (r2 + dr, c2 + dc)):
            if 0 <= row_index < height and 0 <= column_index < width:
                out[row_index][column_index] = color

    return out
