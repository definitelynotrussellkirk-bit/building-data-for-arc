def solve(grid):
    """Expand row-major 2x2 blocks into concentric, quadrant-colored rings."""
    height = len(grid)
    width = len(grid[0])
    if height % 2 or width % 2:
        raise ValueError("The inferred transformation requires even dimensions.")
    if any(len(row) != width for row in grid):
        raise ValueError("The input must be rectangular.")

    result = []
    for block_row in range(0, height, 2):
        for block_col in range(0, width, 2):
            colors = [
                grid[block_row][block_col:block_col + 2],
                grid[block_row + 1][block_col:block_col + 2],
            ]
            size = len(result) + 2
            half = size // 2
            expanded = [
                [colors[int(row >= half)][int(col >= half)]
                 for col in range(size)]
                for row in range(size)
            ]
            for row, values in enumerate(result):
                expanded[row + 1][1:-1] = values
            result = expanded
    return result
