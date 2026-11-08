"""Plausible lesson rival: remove the corner, crop, always reflect horizontally."""


def solve(grid):
    rest = [row[:] for row in grid]
    rest[0][0] = 0
    cells = [(r, c) for r, row in enumerate(rest) for c, v in enumerate(row) if v]
    if not cells:
        return [[0]]
    rows, cols = zip(*cells)
    cropped = [row[min(cols):max(cols)+1] for row in rest[min(rows):max(rows)+1]]
    return [row[::-1] for row in cropped]
