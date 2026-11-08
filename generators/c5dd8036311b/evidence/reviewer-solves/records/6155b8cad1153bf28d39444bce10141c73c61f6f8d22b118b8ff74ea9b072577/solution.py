"""Extend colored markers upward from a horizontal baseline."""
def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected a nonempty rectangular grid')
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        if all(value in (1, 2, 8) for value in row):
            for c, value in enumerate(row):
                height = {2: 4, 8: 3}.get(value, 0)
                for distance in range(1, height + 1):
                    if r - distance >= 0:
                        out[r-distance][c] = value if distance == height else 1
    return out
