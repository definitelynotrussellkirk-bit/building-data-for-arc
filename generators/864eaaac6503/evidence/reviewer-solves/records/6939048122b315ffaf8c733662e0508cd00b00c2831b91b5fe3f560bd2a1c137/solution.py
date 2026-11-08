def solve(grid):
    """Read columns from right to left, preserving top-to-bottom order."""
    if not grid:
        return []
    height, width = len(grid), len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("Expected a rectangular grid")
    return [[grid[r][c] for r in range(height)] for c in range(width - 1, -1, -1)]
