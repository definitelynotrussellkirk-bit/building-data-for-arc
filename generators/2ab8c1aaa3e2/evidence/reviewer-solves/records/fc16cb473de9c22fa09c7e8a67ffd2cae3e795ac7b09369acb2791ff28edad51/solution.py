from collections import defaultdict


def solve(grid):
    """Complete vertical segments whose color occurs exactly twice in a column."""
    out = [row[:] for row in grid]
    if not grid:
        return out

    height = len(grid)
    width = len(grid[0])
    segments = []

    # Infer every segment from the untouched input so painting one segment cannot
    # create a spurious endpoint for another.
    for col in range(width):
        rows_by_color = defaultdict(list)
        for row in range(height):
            color = grid[row][col]
            if color != 0:
                rows_by_color[color].append(row)
        for color, rows in rows_by_color.items():
            if len(rows) == 2:
                segments.append((col, rows[0], rows[1], color))

    for col, start, stop, color in segments:
        for row in range(start, stop + 1):
            out[row][col] = color
    return out
