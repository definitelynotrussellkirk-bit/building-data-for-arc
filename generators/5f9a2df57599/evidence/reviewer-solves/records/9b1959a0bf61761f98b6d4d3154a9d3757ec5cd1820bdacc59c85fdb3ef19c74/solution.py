"""Visible-example hypothesis: fill vertically capped gray pockets yellow."""


def solve(grid):
    h, w = len(grid), len(grid[0])
    result = [list(row) for row in grid]
    seen = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 or (r, c) in seen:
                continue
            cells = [(r, c)]
            seen.add((r, c))
            for y, x in cells:
                for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if 0 <= yy < h and 0 <= xx < w and grid[yy][xx] == 0 and (yy, xx) not in seen:
                        seen.add((yy, xx))
                        cells.append((yy, xx))
            top, bottom = min(y for y, x in cells), max(y for y, x in cells)
            left, right = min(x for y, x in cells), max(x for y, x in cells)
            if top == 0 or bottom == h - 1:
                continue
            caps = all(grid[y][x] == 5 for y in (top - 1, bottom + 1) for x in range(left, right + 1))
            sides = all(grid[y][x] == 5 for x in (left - 1, right + 1) if 0 <= x < w for y in range(top, bottom + 1))
            if caps and sides:
                for y, x in cells:
                    result[y][x] = 4
    return result
