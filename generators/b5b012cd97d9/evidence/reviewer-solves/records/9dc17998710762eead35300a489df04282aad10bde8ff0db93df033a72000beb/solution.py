from collections import Counter
from math import isqrt


def solve(grid):
    """Repack each non-background color into a solid square.

    A color appearing n^2 times becomes an n-by-n block.  Blocks are ordered
    from smallest to largest, bottom-aligned, and separated by one background
    column.
    """
    counts = Counter(cell for row in grid for cell in row)
    background = counts.most_common(1)[0][0]

    blocks = []
    first_seen = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            first_seen.setdefault(color, (r, c))

    for color, count in counts.items():
        if color == background:
            continue
        side = isqrt(count)
        if side * side != count:
            raise ValueError(f"non-background color {color} has non-square count {count}")
        blocks.append((side, first_seen[color], color))

    blocks.sort(key=lambda item: (item[0], item[1], item[2]))
    height = max(side for side, _, _ in blocks)
    width = sum(side for side, _, _ in blocks) + len(blocks) - 1
    out = [[background for _ in range(width)] for _ in range(height)]

    x = 0
    for side, _, color in blocks:
        top = height - side
        for r in range(top, height):
            for c in range(x, x + side):
                out[r][c] = color
        x += side + 1
    return out
