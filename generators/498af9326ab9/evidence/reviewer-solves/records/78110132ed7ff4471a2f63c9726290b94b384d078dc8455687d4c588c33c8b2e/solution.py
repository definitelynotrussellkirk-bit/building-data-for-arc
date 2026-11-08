from collections import deque


def _distances(grid, start):
    """Return 4-neighbour distances through every non-gray cell."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    distances = [[None for _ in range(width)] for _ in range(height)]
    queue = deque([start])
    distances[start[0]][start[1]] = 0

    while queue:
        row, col = queue.popleft()
        next_distance = distances[row][col] + 1
        for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            next_row, next_col = row + drow, col + dcol
            if not (0 <= next_row < height and 0 <= next_col < width):
                continue
            if grid[next_row][next_col] == 5:
                continue
            if distances[next_row][next_col] is not None:
                continue
            distances[next_row][next_col] = next_distance
            queue.append((next_row, next_col))

    return distances


def solve(grid):
    """Color every background cell lying on a shortest 1-to-2 path with 8."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    endpoints = {}
    for row_index, row in enumerate(grid):
        for col_index, color in enumerate(row):
            if color in (1, 2):
                endpoints[color] = (row_index, col_index)

    if 1 not in endpoints or 2 not in endpoints:
        return [row[:] for row in grid]

    from_one = _distances(grid, endpoints[1])
    from_two = _distances(grid, endpoints[2])
    shortest = from_one[endpoints[2][0]][endpoints[2][1]]
    if shortest is None:
        return [row[:] for row in grid]

    result = [row[:] for row in grid]
    for row_index, row in enumerate(grid):
        for col_index, color in enumerate(row):
            distance_one = from_one[row_index][col_index]
            distance_two = from_two[row_index][col_index]
            if (
                color == 0
                and distance_one is not None
                and distance_two is not None
                and distance_one + distance_two == shortest
            ):
                result[row_index][col_index] = 8

    return result
