def solve(grid):
    """Fill a framed interior with a checkerboard keyed by two seed colors."""
    height = len(grid)
    width = len(grid[0]) if height else 0

    frame = None
    for color in range(1, 10):
        cells = {
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == color
        }
        if not cells:
            continue
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)
        if bottom - top < 2 or right - left < 2:
            continue
        border = {
            (row, col)
            for row in range(top, bottom + 1)
            for col in range(left, right + 1)
            if row in (top, bottom) or col in (left, right)
        }
        if cells == border:
            frame = (top, left, bottom, right)
            break

    if frame is None:
        return [row[:] for row in grid]

    top, left, bottom, right = frame
    seeds = [
        (row, col, grid[row][col])
        for row in range(top + 1, bottom)
        for col in range(left + 1, right)
        if grid[row][col] != 0
    ]
    if len(seeds) != 2:
        return [row[:] for row in grid]

    seeds.sort(key=lambda item: (item[1], item[0]))
    left_color = seeds[0][2]
    right_color = seeds[1][2]

    result = [row[:] for row in grid]
    for row in range(top + 1, bottom):
        for col in range(left + 1, right):
            parity = (row - top - 1 + col - left - 1) % 2
            result[row][col] = left_color if parity == 0 else right_color
    return result
