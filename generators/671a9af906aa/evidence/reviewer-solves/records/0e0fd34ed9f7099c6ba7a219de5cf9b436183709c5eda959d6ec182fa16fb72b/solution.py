from collections import deque


def _shortest_path(grid, start, goal):
    """Return one shortest 4-neighbour path through every non-8 cell."""
    height = len(grid)
    width = len(grid[0])
    queue = deque([start])
    parent = {start: None}

    while queue:
        row, col = queue.popleft()
        if (row, col) == goal:
            break
        for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (row + drow, col + dcol)
            nr, nc = nxt
            if (
                0 <= nr < height
                and 0 <= nc < width
                and grid[nr][nc] != 8
                and nxt not in parent
            ):
                parent[nxt] = (row, col)
                queue.append(nxt)

    if goal not in parent:
        return None

    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = parent[current]
    path.reverse()
    return path


def solve(grid):
    """Draw the unique nonintersecting pairing from {2, 5} to {3, 4}."""
    result = [row[:] for row in grid]
    locations = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value in (2, 3, 4, 5):
                locations[value] = (row, col)

    if set(locations) != {2, 3, 4, 5}:
        return result

    # The visible examples support two bipartite perfect matchings.  A matching
    # is usable only when its two routes share no cell (including terminals).
    matchings = (
        ((2, 3), (5, 4)),
        ((2, 4), (5, 3)),
    )
    valid = []
    for first_pair, second_pair in matchings:
        first_path = _shortest_path(
            grid, locations[first_pair[0]], locations[first_pair[1]]
        )
        second_path = _shortest_path(
            grid, locations[second_pair[0]], locations[second_pair[1]]
        )
        if first_path is None or second_path is None:
            continue
        if set(first_path).isdisjoint(second_path):
            valid.append((first_path, second_path))

    # The unchanged training example indicates that an absent (or ambiguous)
    # legal pairing should not be guessed.
    if len(valid) != 1:
        return result

    for path in valid[0]:
        for row, col in path[1:-1]:
            if result[row][col] == 0:
                result[row][col] = 7
    return result
