from __future__ import annotations

from collections import Counter
from math import isqrt
from typing import Sequence


def solve(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Repack each non-background color into a bottom-aligned filled square.

    The most frequent color is the background.  Every other color occurs a
    perfect-square number of times.  Those colors become filled squares ordered
    from smallest to largest, separated by one background column.
    """
    if not grid or not grid[0]:
        return []

    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    counts = Counter(cell for row in grid for cell in row)
    background = max(counts, key=lambda color: (counts[color], -color))

    squares: list[tuple[int, int]] = []
    for color, count in counts.items():
        if color == background:
            continue
        side = isqrt(count)
        if side * side != count:
            raise ValueError(
                f"non-background color {color} has non-square count {count}"
            )
        squares.append((side, color))

    if not squares:
        return []

    squares.sort(key=lambda item: (item[0], item[1]))
    out_height = max(side for side, _ in squares)
    out_width = sum(side for side, _ in squares) + len(squares) - 1
    output = [[background for _ in range(out_width)] for _ in range(out_height)]

    left = 0
    for side, color in squares:
        top = out_height - side
        for row in range(top, out_height):
            for col in range(left, left + side):
                output[row][col] = color
        left += side + 1

    return output
