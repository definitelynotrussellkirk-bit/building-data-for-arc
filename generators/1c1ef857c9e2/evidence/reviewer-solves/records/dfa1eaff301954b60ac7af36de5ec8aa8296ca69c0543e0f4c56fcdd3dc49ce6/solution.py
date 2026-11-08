from collections import Counter


def solve(grid):
    """Compress complete separator lines into a solid section-count grid."""
    if not grid or not grid[0]:
        return []
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    counts = Counter(cell for row in grid for cell in row)
    if len(counts) != 2:
        raise ValueError("expected exactly two colors")
    background, separator = (color for color, _ in counts.most_common())

    separator_rows = sum(all(cell == separator for cell in row) for row in grid)
    separator_cols = sum(
        all(grid[row][col] == separator for row in range(len(grid)))
        for col in range(width)
    )
    return [
        [background for _ in range(separator_cols + 1)]
        for _ in range(separator_rows + 1)
    ]
