from collections import Counter


def solve(grid):
    """Return an 8-filled rectangle matching the odd panel's encoded size."""
    height = len(grid)
    width = len(grid[0]) if height else 0

    divider_cols = [
        col
        for col in range(width)
        if all(grid[row][col] == 9 for row in range(height))
    ]
    boundaries = [-1, *divider_cols, width]
    sizes = []

    for left_divider, right_divider in zip(boundaries, boundaries[1:]):
        points = [
            (row, col)
            for row in range(height)
            for col in range(left_divider + 1, right_divider)
            if grid[row][col] == 2
        ]
        if not points:
            continue
        rows = [row for row, _ in points]
        cols = [col for _, col in points]
        sizes.append((max(rows) - min(rows) + 1, max(cols) - min(cols) + 1))

    counts = Counter(sizes)
    output_height, output_width = next(size for size in sizes if counts[size] == 1)
    return [[8 for _ in range(output_width)] for _ in range(output_height)]
