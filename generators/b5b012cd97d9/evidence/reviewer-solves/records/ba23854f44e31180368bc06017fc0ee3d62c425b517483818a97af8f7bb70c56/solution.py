from collections import Counter
from math import isqrt


def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected a nonempty rectangular grid')
    counts = Counter(cell for row in grid for cell in row)
    bg = counts.most_common(1)[0][0]
    blocks = []
    for color, count in counts.items():
        if color == bg:
            continue
        side = isqrt(count)
        if side * side != count:
            raise ValueError('A foreground color has nonsquare population')
        blocks.append((side, color))
    blocks.sort()
    if not blocks:
        return [[bg]]
    height = max(side for side, _ in blocks)
    width = sum(side for side, _ in blocks) + len(blocks) - 1
    out = [[bg] * width for _ in range(height)]
    left = 0
    for side, color in blocks:
        for r in range(height - side, height):
            out[r][left:left + side] = [color] * side
        left += side + 1
    return out
