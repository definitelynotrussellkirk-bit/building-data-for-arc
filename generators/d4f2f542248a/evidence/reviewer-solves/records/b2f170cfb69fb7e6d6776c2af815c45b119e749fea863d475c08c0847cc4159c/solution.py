"""Visible-example solution for blind task d4f2f542248a.

Cells with value 5 are walls.  Recolor every ordinary passable cell that lies
on every shortest 4-neighbour path from the red endpoint (2) to the green
endpoint (3) with azure (8).  Keep both endpoints unchanged.
"""

from collections import deque


def _distances(grid, start):
    """Return 4-neighbour shortest-path distances through non-wall cells."""
    height = len(grid)
    width = len(grid[0])
    distances = {start: 0}
    queue = deque([start])

    while queue:
        row, col = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = row + dr, col + dc
            if not (0 <= nr < height and 0 <= nc < width):
                continue
            if grid[nr][nc] == 5 or (nr, nc) in distances:
                continue
            distances[(nr, nc)] = distances[(row, col)] + 1
            queue.append((nr, nc))

    return distances


def solve(grid):
    """Mark the mandatory interior cells of all shortest 2-to-3 paths."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    red = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]
    green = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 3
    ]
    result = [row[:] for row in grid]
    if len(red) != 1 or len(green) != 1:
        return result

    source, target = red[0], green[0]
    distance_from_source = _distances(grid, source)
    if target not in distance_from_source:
        return result
    distance_from_target = _distances(grid, target)
    shortest_length = distance_from_source[target]

    shortest_nodes = {
        cell
        for cell, source_distance in distance_from_source.items()
        if source_distance + distance_from_target.get(cell, shortest_length + 1)
        == shortest_length
    }

    # Count shortest prefixes reaching each node in the shortest-path DAG.
    prefixes = {source: 1}
    for cell in sorted(shortest_nodes, key=distance_from_source.get):
        ways = prefixes.get(cell, 0)
        if not ways:
            continue
        row, col = cell
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (row + dr, col + dc)
            if (
                nxt in shortest_nodes
                and distance_from_source[nxt] == distance_from_source[cell] + 1
            ):
                prefixes[nxt] = prefixes.get(nxt, 0) + ways

    # Count shortest suffixes from each node to the target.
    suffixes = {target: 1}
    for cell in sorted(
        shortest_nodes, key=distance_from_source.get, reverse=True
    ):
        ways = suffixes.get(cell, 0)
        if not ways:
            continue
        row, col = cell
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            previous = (row + dr, col + dc)
            if (
                previous in shortest_nodes
                and distance_from_source[previous]
                == distance_from_source[cell] - 1
            ):
                suffixes[previous] = suffixes.get(previous, 0) + ways

    total_shortest_paths = prefixes[target]
    for row, col in shortest_nodes:
        if (
            grid[row][col] == 0
            and prefixes.get((row, col), 0) * suffixes.get((row, col), 0)
            == total_shortest_paths
        ):
            result[row][col] = 8

    return result
