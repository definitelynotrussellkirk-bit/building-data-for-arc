def solve(grid):
    """Expand each observed input cell into a same-colored 4 by 4 block."""
    result = []
    for row in grid:
        expanded_row = [color for color in row for _ in range(4)]
        result.extend(expanded_row[:] for _ in range(4))
    return result
