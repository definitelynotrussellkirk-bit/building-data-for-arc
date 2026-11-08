from collections import defaultdict


def solve(grid):
    """Fill the bounding box of each nonzero color occurring exactly four times."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    by_color = defaultdict(list)
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color != 0:
                by_color[color].append((row, col))

    output = [[0 for _ in range(width)] for _ in range(height)]
    for color, cells in by_color.items():
        if len(cells) != 4:
            continue
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        for row in range(min(rows), max(rows) + 1):
            for col in range(min(cols), max(cols) + 1):
                output[row][col] = color
    return output
