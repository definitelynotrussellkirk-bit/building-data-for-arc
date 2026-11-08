def solve(grid):
    """Return the rectangular grid transposed across its main diagonal."""
    if not grid:
        return []
    return [list(column) for column in zip(*grid)]
