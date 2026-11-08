def solve(grid):
    """Keep each colored cell and add its reflection across the main diagonal."""
    if not grid or any(len(row) != len(grid) for row in grid):
        raise ValueError("Expected a nonempty square grid")
    result = [list(row) for row in grid]
    for row, values in enumerate(grid):
        for column, color in enumerate(values):
            if color != 0:
                result[column][row] = color
    return result
