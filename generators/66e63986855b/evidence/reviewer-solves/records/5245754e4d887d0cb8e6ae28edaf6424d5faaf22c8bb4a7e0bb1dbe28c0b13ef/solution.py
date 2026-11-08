"""Exposed post-repair solve, checked using the visible lesson only."""

def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected a nonempty rectangular grid')
    height, width = len(grid), len(grid[0])
    occupied = [(r, c, value) for r, row in enumerate(grid)
                for c, value in enumerate(row) if value != 0]
    answer = [[0] * width for _ in range(height)]
    if not occupied:
        return answer
    first = min(r for r, c, value in occupied)
    last = max(r for r, c, value in occupied)
    right = max(c for r, c, value in occupied)
    color = occupied[0][2]
    for r in range(first + 1, last):
        marked_columns = [c for c, value in enumerate(grid[r]) if value != 0]
        if marked_columns:
            frontier = max(marked_columns)
            end = min(width - 1, 2 * right - frontier)
            for c in range(frontier + 1, end + 1):
                answer[r][c] = color
    return answer
