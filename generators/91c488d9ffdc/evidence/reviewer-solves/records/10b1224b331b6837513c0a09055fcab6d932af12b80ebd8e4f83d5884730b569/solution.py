from collections import defaultdict


def solve(grid):
    """Replace each same-color opposite-corner pair by its rectangle border."""
    height = len(grid)
    width = len(grid[0])
    positions = defaultdict(list)
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                positions[color].append((row_index, column_index))

    output = [[0 for _ in range(width)] for _ in range(height)]
    for color, cells in positions.items():
        if len(cells) != 2:
            continue
        (r_a, c_a), (r_b, c_b) = cells
        r0, r1 = sorted((r_a, r_b))
        c0, c1 = sorted((c_a, c_b))
        for column in range(c0, c1 + 1):
            output[r0][column] = color
            output[r1][column] = color
        for row in range(r0, r1 + 1):
            output[row][c0] = color
            output[row][c1] = color
    return output
