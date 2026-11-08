from collections import Counter
from copy import deepcopy


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                point = (r + dr, c + dc)
                if point in remaining:
                    remaining.remove(point)
                    stack.append(point)
        result.append(cells)
    return result


def solve(grid):
    if not grid or not grid[0]:
        return deepcopy(grid)

    h, w = len(grid), len(grid[0])
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    output = deepcopy(grid)

    for cells in _components(grid, 1):
        r0 = min(r for r, _ in cells)
        r1 = max(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        c1 = max(c for _, c in cells)
        cellset = set(cells)
        perimeter = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        missing = sorted(perimeter - cellset)
        if len(missing) != 1:
            continue
        gap_r, gap_c = missing[0]

        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                if output[r][c] == background:
                    output[r][c] = 2

        if gap_r == r0:
            beam = ((r, gap_c) for r in range(0, r0 + 1))
        elif gap_r == r1:
            beam = ((r, gap_c) for r in range(r1, h))
        elif gap_c == c0:
            beam = ((gap_r, c) for c in range(0, c0 + 1))
        elif gap_c == c1:
            beam = ((gap_r, c) for c in range(c1, w))
        else:
            continue

        for r, c in beam:
            if output[r][c] == background:
                output[r][c] = 2

    return output
