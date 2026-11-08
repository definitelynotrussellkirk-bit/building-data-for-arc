from collections import deque


def _distances(grid, start):
    height = len(grid)
    width = len(grid[0])
    distances = {start: 0}
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        next_distance = distances[(row, col)] + 1
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = row + dr, col + dc
            if not (0 <= nr < height and 0 <= nc < width):
                continue
            if grid[nr][nc] == 5 or (nr, nc) in distances:
                continue
            distances[(nr, nc)] = next_distance
            queue.append((nr, nc))
    return distances


def solve(grid):
    """Paint open cells equally and finitely reachable from the 2 and 3 seeds."""
    red = next(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    )
    green = next(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 3
    )
    red_distance = _distances(grid, red)
    green_distance = _distances(grid, green)
    output = [list(row) for row in grid]
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            point = (row, col)
            if (
                value == 0
                and point in red_distance
                and point in green_distance
                and red_distance[point] == green_distance[point]
            ):
                output[row][col] = 8
    return output
