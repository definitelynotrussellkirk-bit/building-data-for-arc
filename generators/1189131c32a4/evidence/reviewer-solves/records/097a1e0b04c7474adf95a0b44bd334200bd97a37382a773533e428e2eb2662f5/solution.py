from collections import Counter


def solve(grid):
    """Arrange non-background colors as concentric square rings.

    Colors are ordered by decreasing frequency. Equal-frequency colors keep
    their first row-major appearance order, matching the visible examples.
    """
    if not grid or not grid[0]:
        return []

    counts = Counter(cell for row in grid for cell in row)
    background = max(counts, key=counts.get)

    first_seen = {}
    for row_index, row in enumerate(grid):
        for col_index, color in enumerate(row):
            first_seen.setdefault(color, (row_index, col_index))

    colors = [color for color in counts if color != background]
    colors.sort(key=lambda color: (-counts[color], first_seen[color]))

    size = 2 * len(colors) - 1
    output = [[0] * size for _ in range(size)]
    for row in range(size):
        for col in range(size):
            depth = min(row, col, size - 1 - row, size - 1 - col)
            output[row][col] = colors[depth]
    return output
