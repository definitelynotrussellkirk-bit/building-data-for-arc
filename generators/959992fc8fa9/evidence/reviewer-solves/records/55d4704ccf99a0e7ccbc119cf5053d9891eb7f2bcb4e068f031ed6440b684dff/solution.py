def solve(grid):
    """Extend every colored point across its row and column.

    A cell receives the unique contributing color, or color 2 when crosses of
    different colors intersect. Empty cells with no contributing cross stay 0.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0

    row_colors = [set() for _ in range(height)]
    col_colors = [set() for _ in range(width)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                row_colors[r].add(value)
                col_colors[c].add(value)

    result = [[0 for _ in range(width)] for _ in range(height)]
    for r in range(height):
        for c in range(width):
            contributors = row_colors[r] | col_colors[c]
            if len(contributors) == 1:
                result[r][c] = next(iter(contributors))
            elif len(contributors) > 1:
                result[r][c] = 2
    return result
