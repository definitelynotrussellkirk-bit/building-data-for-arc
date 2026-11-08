"""Example-derived solver for this public challenge; standard library only."""
from collections import Counter


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Keep the input and add a marker-colored copy of the green silhouette.

    The visible third example distinguishes the bounding-box origin from
    the first occupied green cell, and retains markers at an empty corner.
    """
    if not isinstance(grid, list) or not grid or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("expected rectangular rows")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("expected integer colors in 0..9")
    template = [(r, c) for r, row in enumerate(grid)
                for c, color in enumerate(row) if color == 3]
    if not template:
        raise ValueError("green template is missing")
    origin_r = min(r for r, _ in template)
    origin_c = min(c for _, c in template)
    offsets = [(r - origin_r, c - origin_c) for r, c in template]
    markers = [(r, c, color) for r, row in enumerate(grid)
               for c, color in enumerate(row) if color not in (0, 3)]
    if any(count != 1 for count in Counter(v for _, _, v in markers).values()):
        raise ValueError("this hypothesis expects one marker of each marker color")
    output = [row[:] for row in grid]
    for r, c, color in markers:
        for dr, dc in offsets:
            rr, cc = r + dr, c + dc
            if not (0 <= rr < height and 0 <= cc < width):
                raise ValueError("predicted stamp does not fit on this canvas")
            output[rr][cc] = color
    return output
