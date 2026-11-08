"""Visible-only solution for the assigned blind ARC episode."""


def solve(grid):
    """Reverse the order of two-column tiles while preserving each tile."""
    output = []
    for row in grid:
        tiles = [row[index:index + 2] for index in range(0, len(row), 2)]
        output.append([value for tile in reversed(tiles) for value in tile])
    return output
