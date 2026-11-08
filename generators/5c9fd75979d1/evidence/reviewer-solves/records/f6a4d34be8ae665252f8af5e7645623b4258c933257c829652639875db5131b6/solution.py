"""Recover a damaged rectangular color mosaic, compress, and mirror it."""
from collections import Counter


def solve(grid):
    h, w = len(grid), len(grid[0])
    cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not cells:
        return [[0]]
    top = min(r for r, c in cells)
    bottom = max(r for r, c in cells) + 1
    left = min(c for r, c in cells)
    right = max(c for r, c in cells) + 1
    rows = [top] + [
        r for r in range(top + 1, bottom)
        if any(grid[r - 1][c] and grid[r][c]
               and grid[r - 1][c] != grid[r][c]
               for c in range(left, right))
    ] + [bottom]
    cols = [left] + [
        c for c in range(left + 1, right)
        if any(grid[r][c - 1] and grid[r][c]
               and grid[r][c - 1] != grid[r][c]
               for r in range(top, bottom))
    ] + [right]
    result = []
    for a, b in zip(rows, rows[1:]):
        line = []
        for x, y in zip(cols, cols[1:]):
            counts = Counter(grid[r][c] for r in range(a, b)
                             for c in range(x, y) if grid[r][c])
            line.append(counts.most_common(1)[0][0])
        result.append(line[::-1])
    return result
