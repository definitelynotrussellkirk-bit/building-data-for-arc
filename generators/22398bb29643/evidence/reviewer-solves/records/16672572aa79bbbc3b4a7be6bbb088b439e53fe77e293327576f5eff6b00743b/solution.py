"""List monochrome objects in the order their topmost cells are encountered."""


def solve(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    colors = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            colors.append(color)
            seen.add((r, c))
            stack = [(r, c)]
            while stack:
                y, x = stack.pop()
                for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if 0 <= yy < h and 0 <= xx < w and (yy, xx) not in seen and grid[yy][xx] == color:
                        seen.add((yy, xx))
                        stack.append((yy, xx))
    return [colors]
