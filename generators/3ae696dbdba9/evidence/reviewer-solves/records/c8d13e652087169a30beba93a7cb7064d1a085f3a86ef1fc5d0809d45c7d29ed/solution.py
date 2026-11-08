"""Infer vertical gap filling independently within each colored component."""


def solve(grid):
    out = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    seen = set()
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            component = []
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                r, c = stack.pop()
                component.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            spans = {}
            for r, c in component:
                lo, hi = spans.get(c, (r, r))
                spans[c] = min(lo, r), max(hi, r)
            for c, (lo, hi) in spans.items():
                for r in range(lo, hi + 1):
                    if grid[r][c] == 0:
                        out[r][c] = color
    return out
