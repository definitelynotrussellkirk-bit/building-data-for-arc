"""Post-repair solve; earlier rule exposure declared in SOLVE_NOTES.md."""
from math import atan2, tau


def solve(grid):
    height, width = len(grid), len(grid[0])
    hub_r, hub_c = min((r, c) for r, row in enumerate(grid)
                       for c, color in enumerate(row) if color == 9)
    remaining = {(r, c) for r in range(height) for c in range(width)
                 if grid[r][c] not in (0, 9)}
    pieces = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        color = grid[first[0]][first[1]]
        cells, stack = [first], [first]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining and grid[point[0]][point[1]] == color:
                    remaining.remove(point)
                    cells.append(point)
                    stack.append(point)
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        cy, cx = (r0 + r1) / 2, (c0 + c1) / 2
        angle = atan2(cx - hub_c, hub_r - cy) % tau
        pieces.append((angle, r0, c0, r1, c1, color))
    strips = []
    for _, r0, c0, r1, c1, color in sorted(pieces):
        box_h, box_w = r1 - r0 + 1, c1 - c0 + 1
        left = (color == 6 or (color == 2 and box_h < 3 and box_w == 3)
                or (box_w < 3 and (c0 + c1 < 2 * hub_c or r0 + r1 > 2 * hub_r)))
        bottom = min(height - 1, r1 + 1) if box_h < 3 else r1
        start = max(0, c0 - 1) if left else c0
        end = min(width - 1, c1 + 1) if not left and box_w < 3 else c1
        strips.append([list(row[start:end + 1]) for row in grid[r0:bottom + 1]])
    return [sum((list(row) for row in rows), []) for rows in zip(*strips)]
