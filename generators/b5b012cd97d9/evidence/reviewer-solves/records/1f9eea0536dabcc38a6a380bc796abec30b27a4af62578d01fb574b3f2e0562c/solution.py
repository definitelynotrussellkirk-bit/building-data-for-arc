from collections import Counter
from math import isqrt


def solve(grid):
    """Pack non-background colors as solid count-preserving squares."""
    counts = Counter(cell for row in grid for cell in row)
    background = max(counts, key=lambda color: counts[color])

    blocks = []
    for color, count in counts.items():
        if color == background:
            continue
        side = isqrt(count)
        if side * side != count:
            raise ValueError(f"non-background color {color} has non-square count {count}")
        blocks.append((side, color))

    blocks.sort()  # visible examples order squares from smallest to largest
    if not blocks:
        return []

    height = max(side for side, _ in blocks)
    width = sum(side for side, _ in blocks) + len(blocks) - 1
    output = [[background for _ in range(width)] for _ in range(height)]

    left = 0
    for side, color in blocks:
        top = height - side
        for row in range(top, height):
            for col in range(left, left + side):
                output[row][col] = color
        left += side + 1

    return output
