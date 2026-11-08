def solve(grid):
    """Consume orthogonally adjacent red/green pairs.

    For every red (2) touching a green (3) by an edge, erase the red and
    recolor the green azure (8).  All decisions use the original grid so a
    cell's update cannot hide another adjacency.
    """
    if not grid:
        return []

    rows = len(grid)
    cols = len(grid[0])
    result = [row[:] for row in grid]
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    for row in range(rows):
        for col in range(cols):
            color = grid[row][col]
            if color not in (2, 3):
                continue

            counterpart = 3 if color == 2 else 2
            touches_counterpart = any(
                0 <= row + dr < rows
                and 0 <= col + dc < cols
                and grid[row + dr][col + dc] == counterpart
                for dr, dc in directions
            )
            if touches_counterpart:
                result[row][col] = 0 if color == 2 else 8

    return result
