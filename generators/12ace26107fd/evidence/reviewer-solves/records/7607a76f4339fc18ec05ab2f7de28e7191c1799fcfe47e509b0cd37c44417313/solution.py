def solve(grid):
    """Count successive cardinal boundary layers, from outside to inside."""
    remaining = {
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value != 0
    }
    counts = []
    while remaining:
        interior = {
            (row, column)
            for row, column in remaining
            if all(
                neighbor in remaining
                for neighbor in (
                    (row - 1, column),
                    (row + 1, column),
                    (row, column - 1),
                    (row, column + 1),
                )
            )
        }
        counts.append(len(remaining) - len(interior))
        remaining = interior
    return [counts]
