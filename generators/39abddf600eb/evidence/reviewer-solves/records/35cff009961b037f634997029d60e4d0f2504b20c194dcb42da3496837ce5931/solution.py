"""Infer the equal-Manhattan-distance cells between two enclosed markers."""

from collections import Counter


def solve(grid):
    """Preserve the grid and mark the interior distance bisector with color 9."""
    result = [row[:] for row in grid]
    counts = Counter(color for row in grid for color in row if color != 0)
    if not counts:
        return result

    # In the visible examples, the rectangular frame is the dominant nonzero color.
    frame_color = counts.most_common(1)[0][0]
    frame = [
        (r, c)
        for r, row in enumerate(grid)
        for c, color in enumerate(row)
        if color == frame_color
    ]
    top = min(r for r, c in frame)
    bottom = max(r for r, c in frame)
    left = min(c for r, c in frame)
    right = max(c for r, c in frame)

    markers = [
        (r, c)
        for r in range(top + 1, bottom)
        for c in range(left + 1, right)
        if grid[r][c] != 0
    ]
    if len(markers) != 2:
        raise ValueError("Expected two nonzero markers inside the frame")
    (r1, c1), (r2, c2) = markers

    for r in range(top + 1, bottom):
        for c in range(left + 1, right):
            if grid[r][c] == 0:
                d1 = abs(r - r1) + abs(c - c1)
                d2 = abs(r - r2) + abs(c - c2)
                if d1 == d2:
                    result[r][c] = 9
    return result
