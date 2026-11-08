def solve(grid):
    """Remove the two-row color key and recolor the remaining picture."""
    if len(grid) < 2:
        return []

    key = {
        source: target
        for source, target in zip(grid[0], grid[1])
        if source != 0 and target != 0
    }
    return [[key.get(cell, cell) for cell in row] for row in grid[2:]]
