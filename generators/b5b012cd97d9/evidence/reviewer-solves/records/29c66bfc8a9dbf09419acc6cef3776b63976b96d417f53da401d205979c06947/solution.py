from collections import Counter
from math import isqrt


def solve(grid):
    counts = Counter(value for row in grid for value in row)
    background = max(counts, key=counts.get)

    squares = []
    for color, count in counts.items():
        if color == background:
            continue
        side = isqrt(count)
        if side * side != count:
            raise ValueError(f"non-background color {color} has non-square count {count}")
        squares.append((side, color))

    squares.sort()
    height = max(side for side, _ in squares)
    width = sum(side for side, _ in squares) + len(squares) - 1
    output = [[background for _ in range(width)] for _ in range(height)]

    left = 0
    for side, color in squares:
        top = height - side
        for row in range(top, height):
            for col in range(left, left + side):
                output[row][col] = color
        left += side + 1

    return output
