"""Infer a corner triangle from a dominant object and scattered markers.

This program uses only relationships inferred from the visible challenge pairs.
It neither loads example data nor depends on a grid size or particular colors.
"""

from collections import Counter


def solve(grid):
    """Return a new grid with the dominant object and a filled corner triangle.

    The dominant nonzero color is retained.  The other colored cells choose a
    triangle: their mode is its color, one occupied corner is its vertex, and
    their total number minus that corner marker is its leg length.  Color ties
    are resolved by the first occurrence while scanning rows left to right.
    """
    if not grid:
        return []
    height, width = len(grid), len(grid[0])
    if width == 0:
        return [[] for _ in grid]
    if any(len(row) != width for row in grid):
        raise ValueError("The input must be a rectangular grid")

    # Counter preserves insertion order, so max gives the row-major first
    # color when two colors have the same frequency.
    counts = Counter(value for row in grid for value in row if value != 0)
    if not counts:
        return [list(row) for row in grid]
    object_color = max(counts, key=counts.get)
    marker_counts = Counter(
        value for row in grid for value in row
        if value != 0 and value != object_color
    )
    if not marker_counts:
        return [list(row) for row in grid]

    triangle_color = max(marker_counts, key=marker_counts.get)
    side = sum(marker_counts.values()) - 1
    corners = list(dict.fromkeys([
        (0, 0), (0, width - 1),
        (height - 1, 0), (height - 1, width - 1),
    ]))
    anchors = [
        (r, c) for r, c in corners
        if grid[r][c] != 0 and grid[r][c] != object_color
    ]
    if len(anchors) != 1:
        raise ValueError("Expected exactly one non-dominant corner marker")
    anchor_r, anchor_c = anchors[0]

    output = [
        [value if value == object_color else 0 for value in row]
        for row in grid
    ]
    for r in range(height):
        for c in range(width):
            if abs(r - anchor_r) + abs(c - anchor_c) < side:
                output[r][c] = triangle_color
    return output
