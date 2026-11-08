from collections import Counter
from math import isqrt


def solve(grid):
    """Repack each non-background colour into its solid square.

    The most frequent colour is the canvas/background.  Every other colour
    occurs a perfect-square number of times; those squares are arranged from
    smallest to largest, bottom-aligned, with one background column between
    adjacent squares.
    """
    counts = Counter(cell for row in grid for cell in row)
    background = max(counts, key=counts.get)

    squares = []
    for colour, area in counts.items():
        if colour == background:
            continue
        side = isqrt(area)
        if side * side != area:
            raise ValueError(
                f"non-background colour {colour} has non-square area {area}"
            )
        squares.append((side, colour))

    squares.sort()
    if not squares:
        return []

    height = max(side for side, _ in squares)
    width = sum(side for side, _ in squares) + len(squares) - 1
    out = [[background for _ in range(width)] for _ in range(height)]

    x = 0
    for side, colour in squares:
        top = height - side
        for r in range(top, height):
            for c in range(x, x + side):
                out[r][c] = colour
        x += side + 1

    return out
