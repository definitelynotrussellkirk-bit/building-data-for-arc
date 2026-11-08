def solve(grid):
    """Return the isolated 3x3 tile containing the most color-1 cells."""
    height = len(grid)
    width = len(grid[0])
    candidates = []

    for top in range(height - 2):
        for left in range(width - 2):
            tile = [row[left:left + 3] for row in grid[top:top + 3]]
            if any(value == 0 for row in tile for value in row):
                continue

            # The examples present each candidate as a 3x3 nonzero island.
            if top > 0 and any(grid[top - 1][left + dc] != 0 for dc in range(3)):
                continue
            if top + 3 < height and any(grid[top + 3][left + dc] != 0 for dc in range(3)):
                continue
            if left > 0 and any(grid[top + dr][left - 1] != 0 for dr in range(3)):
                continue
            if left + 3 < width and any(grid[top + dr][left + 3] != 0 for dr in range(3)):
                continue

            ones = sum(value == 1 for row in tile for value in row)
            candidates.append((ones, top, left, tile))

    if not candidates:
        raise ValueError("no isolated nonzero 3x3 tile found")

    # max() over only the score would keep the first row-major candidate on ties.
    best_score = max(item[0] for item in candidates)
    for score, _top, _left, tile in candidates:
        if score == best_score:
            return tile

    raise AssertionError("unreachable")
