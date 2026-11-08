def solve(grid):
    """Complement color 8 inside regularly spaced 3-by-3 tile interiors."""
    return [
        [2 if r % 4 and c % 4 and value != 8 else 0
         for c, value in enumerate(row)]
        for r, row in enumerate(grid)
    ]
