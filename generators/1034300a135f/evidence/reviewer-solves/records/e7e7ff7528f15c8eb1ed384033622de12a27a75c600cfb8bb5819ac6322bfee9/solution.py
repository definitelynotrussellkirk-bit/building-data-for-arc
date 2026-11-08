"""Visible-example solution for ARC task 1034300a135f."""
from collections import Counter


def _edge_distance(row: int, col: int, height: int, width: int) -> int:
    return min(row, col, height - 1 - row, width - 1 - col)


def solve(grid):
    """Turn sparse marker colors into concentric rings.

    The dominant nonzero color is the canvas.  Every other cell is a marker,
    including zero.  Read markers row-major, stably order them by their minimum
    distance to an input edge, and use that color sequence for output rings from
    outside inward.  Rings beyond the marker sequence keep the canvas color.
    """
    height = len(grid)
    width = len(grid[0])

    nonzero_counts = Counter(
        value for row in grid for value in row if value != 0
    )
    background = max(nonzero_counts, key=nonzero_counts.get)

    markers = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color != background:
                markers.append(
                    (_edge_distance(row, col, height, width), color)
                )

    # Python's sort is stable, preserving row-major order for equal distances.
    markers.sort(key=lambda item: item[0])
    colors = [color for _distance, color in markers]

    return [
        [
            colors[distance] if distance < len(colors) else background
            for col in range(width)
            for distance in [_edge_distance(row, col, height, width)]
        ]
        for row in range(height)
    ]
