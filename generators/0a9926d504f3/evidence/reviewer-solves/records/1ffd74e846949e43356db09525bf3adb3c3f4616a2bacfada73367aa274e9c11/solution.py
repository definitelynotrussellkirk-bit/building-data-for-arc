"""Visible-example solution for 0a9926d504f3."""
from __future__ import annotations


def solve(grid):
    """Build the extrema-colored frame and the center's color-5 cross."""
    source = [list(row) for row in grid]
    h = len(source)
    w = len(source[0])

    centers = [
        (r, c)
        for r, row in enumerate(source)
        for c, value in enumerate(row)
        if value == 2
    ]
    if len(centers) != 1:
        raise ValueError("expected exactly one color-2 center")
    cr, cc = centers[0]

    markers = [
        (r, c)
        for r, row in enumerate(source)
        for c, value in enumerate(row)
        if value not in (0, 2)
    ]
    if not markers:
        raise ValueError("expected at least one non-center marker")

    # Tuple order supplies the same topmost/leftmost tie break visible in the
    # examples; the generated lessons make each extremal direction unique.
    top = min(markers, key=lambda p: (p[0], p[1]))
    bottom = max(markers, key=lambda p: (p[0], p[1]))
    left = min(markers, key=lambda p: (p[1], p[0]))
    right = max(markers, key=lambda p: (p[1], p[0]))

    top_r, bottom_r = top[0], bottom[0]
    left_c, right_c = left[1], right[1]
    top_color = source[top[0]][top[1]]
    bottom_color = source[bottom[0]][bottom[1]]
    left_color = source[left[0]][left[1]]
    right_color = source[right[0]][right[1]]

    out = [[0 for _ in range(w)] for _ in range(h)]
    for r in range(h):
        for c in range(w):
            # Edge precedence is established by examples 1 and 3: the top and
            # bottom colors own corners, then left, then right.
            if r == top_r and left_c <= c <= right_c:
                out[r][c] = top_color
            elif r == bottom_r and left_c <= c <= right_c:
                out[r][c] = bottom_color
            elif c == left_c and top_r <= r <= bottom_r:
                out[r][c] = left_color
            elif c == right_c and top_r <= r <= bottom_r:
                out[r][c] = right_color
            elif r == cr and c == cc:
                out[r][c] = 2
            elif r == cr and left_c < c < right_c:
                out[r][c] = 5
            elif c == cc and top_r < r < bottom_r:
                out[r][c] = 5
    return out
