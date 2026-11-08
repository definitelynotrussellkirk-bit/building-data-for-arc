"""Compare occupancy of the two panels separated by a full column of 4s."""

def solve(grid):
    if not grid or not grid[0]:
        return []
    separators = [c for c in range(len(grid[0])) if all(row[c] == 4 for row in grid)]
    if len(separators) != 1:
        raise ValueError("expected one full color-4 separator")
    separator = separators[0]
    if len(grid[0]) != 2 * separator + 1:
        raise ValueError("expected equally sized panels")
    return [[2 if (row[c] != 0) != (row[separator + 1 + c] != 0) else 0
             for c in range(separator)] for row in grid]
