from collections import Counter


def solve(grid):
    height, width = len(grid), len(grid[0])
    separators = [c for c in range(width)
                  if all(grid[r][c] == 9 for r in range(height))]
    boundaries = [-1, *separators, width]
    rectangles = []
    for left, right in zip(boundaries, boundaries[1:]):
        if right == left + 1:
            continue
        points = [(r, c) for r in range(height) for c in range(left + 1, right)
                  if grid[r][c] == 2]
        if not points:
            continue
        rows, cols = zip(*points)
        rectangles.append((max(rows) - min(rows) + 1,
                           max(cols) - min(cols) + 1))
    counts = Counter(rectangles)
    distinct = [size for size, count in counts.items() if count == 1]
    if len(rectangles) != 3 or len(distinct) != 1:
        raise ValueError("Expected three panels with one distinct rectangle")
    rows, cols = distinct[0]
    return [[8 for _ in range(cols)] for _ in range(rows)]
