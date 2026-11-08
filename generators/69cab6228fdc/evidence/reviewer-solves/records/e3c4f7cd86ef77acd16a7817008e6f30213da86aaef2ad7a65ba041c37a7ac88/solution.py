"""Visible-example inference: apply the two-row palette key to the body."""
def solve(grid):
    if len(grid) < 4 or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected a rectangular grid with key, separator, and body')
    replacements = {source: target for source, target in zip(grid[0], grid[1]) if source != 0}
    return [[replacements.get(value, value) for value in row] for row in grid[3:]]
