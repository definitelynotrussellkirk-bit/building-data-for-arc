def solve(grid):
    """Recolor body objects in left-edge order using the visible top legend."""
    height, width = len(grid), len(grid[0])
    legend = [value for value in grid[0] if value != 0]
    unseen = {(r, c) for r in range(1, height) for c in range(width)
              if grid[r][c] == 1}
    objects = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        pending = [start]
        cells = []
        while pending:
            r, c = pending.pop()
            cells.append((r, c))
            for point in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if point in unseen:
                    unseen.remove(point)
                    pending.append(point)
        objects.append(cells)
    objects.sort(key=lambda cells: min(c for r, c in cells))
    if len(objects) != len(legend):
        raise ValueError('The visible legend and body object counts differ')
    result = [list(row) for row in grid]
    for color, cells in zip(legend, objects):
        for r, c in cells:
            result[r][c] = color
    return result
