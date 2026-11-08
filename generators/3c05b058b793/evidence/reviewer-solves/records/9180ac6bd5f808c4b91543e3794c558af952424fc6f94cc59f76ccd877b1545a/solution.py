from collections import deque


def _distances(grid, start):
    """Four-neighbour shortest-path distances, treating color 5 as a wall."""
    height = len(grid)
    width = len(grid[0])
    inf = height * width + 1
    distances = [[inf for _ in range(width)] for _ in range(height)]
    queue = deque([start])
    distances[start[0]][start[1]] = 0

    while queue:
        row, col = queue.popleft()
        next_distance = distances[row][col] + 1
        for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nrow, ncol = row + drow, col + dcol
            if not (0 <= nrow < height and 0 <= ncol < width):
                continue
            if grid[nrow][ncol] == 5 or distances[nrow][ncol] != inf:
                continue
            distances[nrow][ncol] = next_distance
            queue.append((nrow, ncol))

    return distances


def solve(grid):
    """Color each empty cell by its nearest seed through the non-wall maze.

    Color 2 claims cells with color 8, color 3 claims cells with color 4, and
    equal-distance cells remain 0.  Seed cells and color-5 walls are preserved.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    red = None
    green = None
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 2:
                red = (row, col)
            elif value == 3:
                green = (row, col)

    if red is None or green is None:
        return [row[:] for row in grid]

    red_distance = _distances(grid, red)
    green_distance = _distances(grid, green)
    output = [row[:] for row in grid]

    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                continue
            if red_distance[row][col] < green_distance[row][col]:
                output[row][col] = 8
            elif green_distance[row][col] < red_distance[row][col]:
                output[row][col] = 4

    return output
