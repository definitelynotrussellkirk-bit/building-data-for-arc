def solve(grid):
    """Preserve the visible grid and turn its colored shape through the 9 point."""
    h = len(grid)
    w = len(grid[0])
    anchors = [(r, c) for r, row in enumerate(grid)
               for c, value in enumerate(row) if value == 9]
    if len(anchors) != 1:
        raise ValueError("Expected the single visible 9 anchor")
    ar, ac = anchors[0]
    answer = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 9):
                continue
            rr, cc = 2 * ar - r, 2 * ac - c
            if 0 <= rr < h and 0 <= cc < w:
                answer[rr][cc] = value
    return answer
