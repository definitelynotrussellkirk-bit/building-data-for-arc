from collections import deque


def _distances(grid, source, wall=5):
    """Return unweighted 4-neighbour distances through every non-wall cell."""
    height = len(grid)
    width = len(grid[0])
    distances = [[None] * width for _ in range(height)]
    queue = deque([source])
    distances[source[0]][source[1]] = 0

    while queue:
        row, col = queue.popleft()
        next_distance = distances[row][col] + 1
        for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nrow, ncol = row + drow, col + dcol
            if not (0 <= nrow < height and 0 <= ncol < width):
                continue
            if grid[nrow][ncol] == wall or distances[nrow][ncol] is not None:
                continue
            distances[nrow][ncol] = next_distance
            queue.append((nrow, ncol))

    return distances


def solve(grid):
    """Color the union of all shortest open-cell paths from 2 to 3 with 8."""
    starts = []
    ends = []
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 2:
                starts.append((row, col))
            elif value == 3:
                ends.append((row, col))

    if len(starts) != 1 or len(ends) != 1:
        return [row[:] for row in grid]

    start, end = starts[0], ends[0]
    from_start = _distances(grid, start)
    from_end = _distances(grid, end)
    shortest = from_start[end[0]][end[1]]
    if shortest is None:
        return [row[:] for row in grid]

    output = [row[:] for row in grid]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] != 0:
                continue
            left = from_start[row][col]
            right = from_end[row][col]
            if left is not None and right is not None and left + right == shortest:
                output[row][col] = 8

    return output
