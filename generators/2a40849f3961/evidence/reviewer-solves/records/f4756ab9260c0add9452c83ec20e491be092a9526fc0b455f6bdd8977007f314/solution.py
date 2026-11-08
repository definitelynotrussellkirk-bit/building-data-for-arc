from collections import deque


def _find(grid, color):
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == color:
                return row, col
    raise ValueError(f"missing checkpoint {color}")


def _shortest_path(grid, start, goal):
    """BFS through non-5 cells; visible ties choose up, down, left, right."""
    height, width = len(grid), len(grid[0])
    queue = deque([start])
    parent = {start: None}
    for row, col in queue:
        if (row, col) == goal:
            break
        for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neighbor = row + delta_row, col + delta_col
            if (
                0 <= neighbor[0] < height
                and 0 <= neighbor[1] < width
                and grid[neighbor[0]][neighbor[1]] != 5
                and neighbor not in parent
            ):
                parent[neighbor] = (row, col)
                queue.append(neighbor)
    if goal not in parent:
        return []
    path = []
    point = goal
    while point is not None:
        path.append(point)
        point = parent[point]
    return list(reversed(path))


def solve(grid):
    positions = {color: _find(grid, color) for color in (1, 2, 3, 4)}
    output = [list(row) for row in grid]
    route = set()
    for first, second in ((1, 2), (2, 3), (3, 4)):
        route.update(_shortest_path(grid, positions[first], positions[second])[1:-1])
    for row, col in route:
        if output[row][col] == 0:
            output[row][col] = 8
    return output
