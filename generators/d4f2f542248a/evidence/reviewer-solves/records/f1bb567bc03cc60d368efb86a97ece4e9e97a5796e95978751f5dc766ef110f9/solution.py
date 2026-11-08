from collections import deque


def _distances(grid, start):
    height = len(grid)
    width = len(grid[0])
    distances = {start: 0}
    queue = deque([start])

    while queue:
        row, column = queue.popleft()
        next_distance = distances[(row, column)] + 1
        for row_step, column_step in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neighbor = (row + row_step, column + column_step)
            neighbor_row, neighbor_column = neighbor
            if not (0 <= neighbor_row < height and 0 <= neighbor_column < width):
                continue
            if grid[neighbor_row][neighbor_column] == 5 or neighbor in distances:
                continue
            distances[neighbor] = next_distance
            queue.append(neighbor)

    return distances


def solve(grid):
    """Color cells that every shortest path from 3 to 2 must traverse."""
    result = [row[:] for row in grid]
    if not grid or not grid[0]:
        return result

    start = None
    target = None
    for row, values in enumerate(grid):
        for column, value in enumerate(values):
            if value == 3:
                start = (row, column)
            elif value == 2:
                target = (row, column)

    if start is None or target is None:
        return result

    from_start = _distances(grid, start)
    if target not in from_start:
        return result
    from_target = _distances(grid, target)
    shortest_length = from_start[target]

    shortest_path_cells = {
        cell
        for cell, start_distance in from_start.items()
        if cell in from_target
        and start_distance + from_target[cell] == shortest_length
    }

    paths_from_start = {start: 1}
    ordered_cells = sorted(shortest_path_cells, key=from_start.__getitem__)
    for row, column in ordered_cells:
        cell = (row, column)
        if cell == start:
            continue
        previous_distance = from_start[cell] - 1
        paths_from_start[cell] = sum(
            paths_from_start.get((row + row_step, column + column_step), 0)
            for row_step, column_step in ((-1, 0), (1, 0), (0, -1), (0, 1))
            if from_start.get((row + row_step, column + column_step))
            == previous_distance
        )

    paths_to_target = {target: 1}
    for row, column in reversed(ordered_cells):
        cell = (row, column)
        if cell == target:
            continue
        next_distance = from_start[cell] + 1
        paths_to_target[cell] = sum(
            paths_to_target.get((row + row_step, column + column_step), 0)
            for row_step, column_step in ((-1, 0), (1, 0), (0, -1), (0, 1))
            if from_start.get((row + row_step, column + column_step))
            == next_distance
            and (row + row_step, column + column_step) in shortest_path_cells
        )

    total_shortest_paths = paths_from_start[target]
    for row, column in shortest_path_cells:
        cell = (row, column)
        if cell in (start, target):
            continue
        if paths_from_start[cell] * paths_to_target[cell] == total_shortest_paths:
            result[row][column] = 8

    return result
