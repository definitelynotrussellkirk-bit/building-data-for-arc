from collections import deque


def solve(grid):
    """Recolor the non-wall region containing the red seed.

    Color 5 is an impassable wall.  Starting from the unique color-2 cell,
    traverse orthogonally through every non-5 cell and paint the reached
    region color 8.  All walls and disconnected regions are left unchanged.
    """
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    if width == 0:
        return [[] for _ in grid]
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    seeds = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    ]
    if len(seeds) != 1:
        raise ValueError("expected exactly one color-2 seed")

    result = [row[:] for row in grid]
    queue = deque(seeds)
    seen = set(seeds)

    while queue:
        row, col = queue.popleft()
        result[row][col] = 8
        for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            next_row = row + drow
            next_col = col + dcol
            if not (0 <= next_row < height and 0 <= next_col < width):
                continue
            if (next_row, next_col) in seen:
                continue
            if grid[next_row][next_col] == 5:
                continue
            seen.add((next_row, next_col))
            queue.append((next_row, next_col))

    return result
