def solve(grid):
    """Paint cells seen by at least two yellow (4) rook rays.

    Gray cells (5) are opaque blockers. Yellow cells do not block one another,
    and a yellow cell does not count itself as one of the two rays.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0

    row_counts = [[0] * width for _ in range(height)]
    for r, row in enumerate(grid):
        start = 0
        while start < width:
            if row[start] == 5:
                start += 1
                continue
            end = start
            while end < width and row[end] != 5:
                end += 1
            yellows = sum(value == 4 for value in row[start:end])
            for c in range(start, end):
                row_counts[r][c] = yellows
            start = end

    col_counts = [[0] * width for _ in range(height)]
    for c in range(width):
        start = 0
        while start < height:
            if grid[start][c] == 5:
                start += 1
                continue
            end = start
            while end < height and grid[end][c] != 5:
                end += 1
            yellows = sum(grid[r][c] == 4 for r in range(start, end))
            for r in range(start, end):
                col_counts[r][c] = yellows
            start = end

    output = [[0] * width for _ in range(height)]
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 5:
                continue
            aligned = row_counts[r][c] + col_counts[r][c]
            if grid[r][c] == 4:
                aligned -= 2  # The cell's own marker appears in both counts.
            if aligned >= 2:
                output[r][c] = 2
    return output
