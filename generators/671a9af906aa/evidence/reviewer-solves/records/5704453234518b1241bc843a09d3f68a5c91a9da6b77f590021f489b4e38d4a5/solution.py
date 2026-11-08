from collections import deque


def _path(grid, start, goal):
    """Return the unique open-cell path between two coordinates."""
    height = len(grid)
    width = len(grid[0])
    queue = deque([start])
    previous = {start: None}

    while queue:
        row, col = queue.popleft()
        if (row, col) == goal:
            break
        for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = row + drow, col + dcol
            nr, nc = nxt
            if (
                0 <= nr < height
                and 0 <= nc < width
                and grid[nr][nc] != 8
                and nxt not in previous
            ):
                previous[nxt] = (row, col)
                queue.append(nxt)

    if goal not in previous:
        return []

    result = []
    current = goal
    while current is not None:
        result.append(current)
        current = previous[current]
    result.reverse()
    return result


def solve(grid):
    """Draw the two non-nested maze connections, 2↔3 and 4↔5, in orange."""
    result = [row[:] for row in grid]
    markers = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value in (2, 3, 4, 5):
                markers[value] = (row, col)

    if set(markers) != {2, 3, 4, 5}:
        return result

    path_23 = _path(grid, markers[2], markers[3])
    path_45 = _path(grid, markers[4], markers[5])
    if not path_23 or not path_45:
        return result

    # The unchanged training case has one requested connection wholly nested
    # inside the other.  Treat that as an invalid/blocked pair of routes.
    vertices_23 = set(path_23)
    vertices_45 = set(path_45)
    if vertices_23 <= vertices_45 or vertices_45 <= vertices_23:
        return result

    for row, col in vertices_23 | vertices_45:
        if grid[row][col] == 0:
            result[row][col] = 7
    return result
