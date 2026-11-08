from collections import defaultdict


def solve(grid):
    """Connect each equal-colored pair when its endpoints share a 45° diagonal."""
    out = [row[:] for row in grid]
    positions = defaultdict(list)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                positions[color].append((r, c))

    for color, cells in positions.items():
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        dr = r2 - r1
        dc = c2 - c1
        if abs(dr) != abs(dc) or dr == 0:
            continue
        step_r = 1 if dr > 0 else -1
        step_c = 1 if dc > 0 else -1
        for offset in range(1, abs(dr)):
            out[r1 + offset * step_r][c1 + offset * step_c] = color

    return out
