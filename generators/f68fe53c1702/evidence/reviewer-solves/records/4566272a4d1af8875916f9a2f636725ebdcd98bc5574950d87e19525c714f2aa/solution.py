def solve(grid):
    height, width = len(grid), len(grid[0])
    marked = [(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0]
    if not marked:
        return [row[:] for row in grid]
    top = min(r for r, c in marked)
    bottom = max(r for r, c in marked)
    left = min(c for r, c in marked)
    right = max(c for r, c in marked)
    ink = grid[marked[0][0]][marked[0][1]]
    answer = [[0 for c in range(width)] for r in range(height)]
    for r in range(top, bottom + 1):
        for c in range(left, right + 1):
            if r in (top, bottom) or c in (left, right):
                answer[r][c] = ink
    return answer
