def solve(grid):
    """Fill every complete monochrome rectangular frame in the input."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    colors = sorted({cell for row in grid for cell in row if cell != 0})

    for color in colors:
        for top in range(height - 2):
            for bottom in range(top + 2, height):
                for left in range(width - 2):
                    for right in range(left + 2, width):
                        perimeter = (
                            [(top, col) for col in range(left, right + 1)]
                            + [(bottom, col) for col in range(left, right + 1)]
                            + [(row, left) for row in range(top + 1, bottom)]
                            + [(row, right) for row in range(top + 1, bottom)]
                        )
                        if not all(grid[row][col] == color for row, col in perimeter):
                            continue
                        for row in range(top + 1, bottom):
                            for col in range(left + 1, right):
                                out[row][col] = color

    return out
