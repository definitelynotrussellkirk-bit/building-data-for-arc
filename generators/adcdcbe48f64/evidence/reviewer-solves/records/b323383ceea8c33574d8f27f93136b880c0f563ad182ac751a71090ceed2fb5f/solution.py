def solve(grid):
    """Repeat the tile five times horizontally, mirroring every even copy."""
    return [
        list(row) + list(reversed(row)) + list(row) + list(reversed(row)) + list(row)
        for row in grid
    ]
