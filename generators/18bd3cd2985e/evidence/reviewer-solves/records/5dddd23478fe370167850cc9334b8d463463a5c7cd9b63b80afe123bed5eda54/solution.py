"""Reviewer-authored solution from the displayed post-repair examples."""
from collections import Counter


def solve(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    rectangles = []
    scattered = Counter()
    out = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            component = []
            while stack:
                r, c = stack.pop()
                component.append((r, c))
                for nr, nc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            if len(component) == 1:
                scattered[color] += 1
                out[row][col] = 0
            else:
                top = min(r for r, c in component)
                bottom = max(r for r, c in component)
                left = min(c for r, c in component)
                right = max(c for r, c in component)
                places = [(r, c) for r in range(top+1, bottom)
                          for c in range(left+1, right)
                          if (r-top-1+c-left-1) % 2 == 0]
                rectangles.append(places)
    for color, count in scattered.items():
        for places in rectangles:
            if len(places) == count:
                for r, c in places:
                    out[r][c] = color
                break
    return out
