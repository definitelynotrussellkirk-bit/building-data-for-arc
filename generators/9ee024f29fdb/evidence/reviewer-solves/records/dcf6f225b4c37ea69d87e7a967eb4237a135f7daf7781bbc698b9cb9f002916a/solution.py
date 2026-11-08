def solve(grid):
    """Apply the visible 4-spaced lattice / cyan-complement transform."""
    return [
        [
            0 if row_index % 4 == 0 or col_index % 4 == 0 or value == 8 else 2
            for col_index, value in enumerate(row)
        ]
        for row_index, row in enumerate(grid)
    ]
