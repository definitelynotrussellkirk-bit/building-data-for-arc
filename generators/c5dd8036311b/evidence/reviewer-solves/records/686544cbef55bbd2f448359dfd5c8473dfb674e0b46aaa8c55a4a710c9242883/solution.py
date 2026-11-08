def solve(grid):
    """Grow a color-specific vertical mast above every colored marker."""
    result = [row[:] for row in grid]
    top_distances = {2: 4, 8: 3}

    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            distance = top_distances.get(color)
            if distance is None:
                continue
            for step in range(1, distance):
                result[row_index - step][column_index] = 1
            result[row_index - distance][column_index] = color

    return result
