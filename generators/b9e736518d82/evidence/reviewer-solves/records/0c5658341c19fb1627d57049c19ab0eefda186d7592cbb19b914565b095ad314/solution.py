"""Visible-example solution for the prepared ARC episode.

The 7-cells form the two walls of a one-cell-wide, orthogonal channel.
Candidate channel cells are precisely the non-7 cells with two orthogonal
7-neighbours; the true channel is the largest 4-connected component of those
candidates.  A 9 marker on a straight segment leaves the whole channel active.
A 9 marker at a bend splits the ordered channel and activates only the longer
side, while the marker itself remains 9.
"""

from __future__ import annotations

from collections import deque
from typing import Iterable

Coord = tuple[int, int]
_DIRS: tuple[Coord, ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _neighbours(cell: Coord, height: int, width: int) -> Iterable[Coord]:
    row, col = cell
    for drow, dcol in _DIRS:
        nrow, ncol = row + drow, col + dcol
        if 0 <= nrow < height and 0 <= ncol < width:
            yield nrow, ncol


def _channel_component(grid: list[list[int]]) -> set[Coord]:
    height, width = len(grid), len(grid[0])
    candidates: set[Coord] = set()
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 7:
                continue
            wall_count = sum(
                grid[nrow][ncol] == 7
                for nrow, ncol in _neighbours((row, col), height, width)
            )
            if wall_count == 2:
                candidates.add((row, col))

    components: list[set[Coord]] = []
    unseen = set(candidates)
    while unseen:
        start = min(unseen)
        component = {start}
        unseen.remove(start)
        queue = deque([start])
        while queue:
            cell = queue.popleft()
            for neighbour in _neighbours(cell, height, width):
                if neighbour in unseen:
                    unseen.remove(neighbour)
                    component.add(neighbour)
                    queue.append(neighbour)
        components.append(component)

    if not components:
        return set()
    return max(components, key=lambda component: (len(component), tuple(sorted(component))))


def _order_path(component: set[Coord], height: int, width: int) -> list[Coord]:
    if not component:
        return []

    adjacency = {
        cell: sorted(
            neighbour
            for neighbour in _neighbours(cell, height, width)
            if neighbour in component
        )
        for cell in component
    }
    endpoints = sorted(cell for cell, neighbours in adjacency.items() if len(neighbours) <= 1)
    start = endpoints[0] if endpoints else min(component)

    ordered: list[Coord] = []
    previous: Coord | None = None
    current = start
    visited: set[Coord] = set()
    while current not in visited:
        ordered.append(current)
        visited.add(current)
        choices = [cell for cell in adjacency[current] if cell != previous and cell not in visited]
        if not choices:
            break
        previous, current = current, choices[0]

    # The prepared examples use a simple path.  This guard keeps every channel
    # cell represented deterministically if malformed input ever creates a branch.
    if len(ordered) != len(component):
        ordered.extend(sorted(component - set(ordered)))
    return ordered


def solve(grid: list[list[int]]) -> list[list[int]]:
    output = [row[:] for row in grid]
    if not grid or not grid[0]:
        return output

    height, width = len(grid), len(grid[0])
    channel = _channel_component(grid)
    ordered = _order_path(channel, height, width)
    if not ordered:
        return output

    marker_indices = [index for index, (row, col) in enumerate(ordered) if grid[row][col] == 9]
    cells_to_fill: list[Coord]

    if not marker_indices:
        cells_to_fill = ordered
    else:
        marker_index = marker_indices[0]
        if 0 < marker_index < len(ordered) - 1:
            previous = ordered[marker_index - 1]
            marker = ordered[marker_index]
            following = ordered[marker_index + 1]
            straight = (
                previous[0] == marker[0] == following[0]
                or previous[1] == marker[1] == following[1]
            )
        else:
            straight = True

        if straight:
            cells_to_fill = ordered
        else:
            before = ordered[:marker_index]
            after = ordered[marker_index + 1 :]
            cells_to_fill = before if len(before) > len(after) else after

    for row, col in cells_to_fill:
        output[row][col] = 8
    return output
