"""Visible-example hypothesis: crop nonzero support, then rotate clockwise."""
def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected a nonempty rectangular grid')
    points = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if not points:
        return [[0]]
    top, bottom = min(r for r, c in points), max(r for r, c in points)
    left, right = min(c for r, c in points), max(c for r, c in points)
    crop = [row[left:right + 1] for row in grid[top:bottom + 1]]
    return [list(column) for column in zip(*crop[::-1])]
