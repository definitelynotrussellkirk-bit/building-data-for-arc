from collections import deque


def _distances(grid, start):
    height = len(grid)
    width = len(grid[0])
    distances = {start: 0}
    queue = deque([start])

    while queue:
        row, col = queue.popleft()
        for d_row, d_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (row + d_row, col + d_col)
            n_row, n_col = nxt
            if not (0 <= n_row < height and 0 <= n_col < width):
                continue
            if grid[n_row][n_col] == 5 or nxt in distances:
                continue
            distances[nxt] = distances[(row, col)] + 1
            queue.append(nxt)

    return distances


def _shortest_path_counts(shortest_cells, distances, start):
    counts = {start: 1}
    for cell in sorted(shortest_cells, key=distances.__getitem__):
        if cell == start:
            continue
        row, col = cell
        previous = (
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        )
        counts[cell] = sum(
            counts.get(candidate, 0)
            for candidate in previous
            if candidate in shortest_cells
            and distances.get(candidate) == distances[cell] - 1
        )
    return counts


def solve(grid):
    """Color zero cells that every shortest 4-neighbor route must cross."""
    height = len(grid)
    width = len(grid[0])
    endpoints = {
        value: (row, col)
        for row in range(height)
        for col in range(width)
        if (value := grid[row][col]) in (2, 3)
    }
    start = endpoints[3]
    target = endpoints[2]

    from_start = _distances(grid, start)
    from_target = _distances(grid, target)
    shortest_length = from_start[target]
    shortest_cells = {
        cell
        for cell, start_distance in from_start.items()
        if cell in from_target
        and start_distance + from_target[cell] == shortest_length
    }

    prefix_counts = _shortest_path_counts(shortest_cells, from_start, start)
    suffix_counts = _shortest_path_counts(shortest_cells, from_target, target)
    total_shortest_paths = prefix_counts[target]

    result = [row[:] for row in grid]
    for row, col in shortest_cells:
        if (
            grid[row][col] == 0
            and prefix_counts[(row, col)] * suffix_counts[(row, col)]
            == total_shortest_paths
        ):
            result[row][col] = 8
    return result
