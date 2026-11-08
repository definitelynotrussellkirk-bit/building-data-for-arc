from collections import deque


def _find_unique(grid, color):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]
    if len(cells) != 1:
        raise ValueError(f"expected exactly one cell of color {color}, found {len(cells)}")
    return cells[0]


def _distances(grid, start):
    height = len(grid)
    width = len(grid[0])
    distances = [[-1] * width for _ in range(height)]
    distances[start[0]][start[1]] = 0
    queue = deque([start])

    while queue:
        row, col = queue.popleft()
        next_distance = distances[row][col] + 1
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = row + dr, col + dc
            if not (0 <= nr < height and 0 <= nc < width):
                continue
            if grid[nr][nc] == 5 or distances[nr][nc] != -1:
                continue
            distances[nr][nc] = next_distance
            queue.append((nr, nc))

    return distances


def solve(grid):
    """Color the union of all shortest obstacle-avoiding paths from 1 to 2."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be a non-empty rectangle")

    start = _find_unique(grid, 1)
    goal = _find_unique(grid, 2)
    from_start = _distances(grid, start)
    from_goal = _distances(grid, goal)
    shortest = from_start[goal[0]][goal[1]]
    if shortest < 0:
        return [row[:] for row in grid]

    output = [row[:] for row in grid]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] in (1, 2, 5):
                continue
            if (
                from_start[row][col] >= 0
                and from_goal[row][col] >= 0
                and from_start[row][col] + from_goal[row][col] == shortest
            ):
                output[row][col] = 8

    return output
