"""Exposed post-repair attempt, written from the visible challenge."""
from collections import defaultdict


def solve(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    by_span = defaultdict(list)
    for row in range(h):
        for col in range(w):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            todo = [(row, col)]
            seen.add((row, col))
            cells = []
            while todo:
                r, c = todo.pop()
                cells.append((r, c))
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= rr < h and 0 <= cc < w and (rr, cc) not in seen
                            and grid[rr][cc] == color):
                        seen.add((rr, cc))
                        todo.append((rr, cc))
            rows = [r for r, c in cells]
            columns = {c for r, c in cells}
            if len(columns) == 1 and len(cells) >= 2:
                top, bottom = min(rows), max(rows)
                if bottom - top + 1 == len(cells):
                    by_span[(color, top, bottom)].append(next(iter(columns)))
    output = [list(row) for row in grid]
    for (color, top, bottom), columns in by_span.items():
        columns.sort()
        for index in range(0, len(columns) - 1, 2):
            left, right = columns[index:index + 2]
            for r in range(top, bottom + 1):
                for c in range(left, right + 1):
                    output[r][c] = color
    return output
