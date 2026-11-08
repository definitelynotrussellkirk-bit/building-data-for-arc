"""Visible-example-only candidate for blind task 28ba67946524.

The inputs contain one largest multicoloured connected object and one or more
smaller detached clues.  The visible examples consistently select monochrome
regions inside the large object:

* for a one-cell-wide strip, the third colour run in reading order;
* for a wider object, the highest-labelled region in each row band containing
  two or more side-by-side regions.

The numerical comparison in the second case is only a visible-example
hypothesis; no hidden rule or labels were consulted.
"""

from __future__ import annotations

from collections import deque
from typing import Iterable

Grid = list[list[int]]
Point = tuple[int, int]


def _components(grid: Grid, *, same_colour: bool) -> list[list[Point]]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[Point] = set()
    result: list[list[Point]] = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            colour = grid[row][col]
            queue: deque[Point] = deque([(row, col)])
            seen.add((row, col))
            component: list[Point] = []

            while queue:
                current_row, current_col = queue.popleft()
                component.append((current_row, current_col))
                for row_delta, col_delta in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + row_delta
                    next_col = current_col + col_delta
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen or grid[next_row][next_col] == 0:
                        continue
                    if same_colour and grid[next_row][next_col] != colour:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            result.append(component)

    return result


def _bounds(points: Iterable[Point]) -> tuple[int, int, int, int]:
    points = list(points)
    rows = [point[0] for point in points]
    cols = [point[1] for point in points]
    return min(rows), min(cols), max(rows), max(cols)


def solve(grid: Grid) -> Grid:
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]

    nonzero_components = _components(grid, same_colour=False)
    if not nonzero_components:
        return output
    main = max(nonzero_components, key=len)
    main_points = set(main)
    min_row, min_col, max_row, max_col = _bounds(main)

    colour_regions: list[tuple[int, list[Point], tuple[int, int, int, int]]] = []
    for component in _components(grid, same_colour=True):
        if set(component) <= main_points:
            row, col = component[0]
            colour_regions.append((grid[row][col], component, _bounds(component)))

    selected: list[Point] = []

    if min_col == max_col:
        ordered = sorted(colour_regions, key=lambda item: (item[2][0], item[2][1]))
        if ordered:
            selected.extend(ordered[min(2, len(ordered) - 1)][1])
    elif min_row == max_row:
        ordered = sorted(colour_regions, key=lambda item: (item[2][1], item[2][0]))
        if ordered:
            selected.extend(ordered[min(2, len(ordered) - 1)][1])
    else:
        bands: dict[tuple[int, int], list[tuple[int, list[Point], tuple[int, int, int, int]]]] = {}
        for region in colour_regions:
            bounds = region[2]
            bands.setdefault((bounds[0], bounds[2]), []).append(region)

        for band in bands.values():
            if len(band) < 2:
                continue
            selected.extend(max(band, key=lambda item: item[0])[1])

        if not selected and colour_regions:
            centre_row = (min_row + max_row) / 2
            centre_col = (min_col + max_col) / 2
            closest = min(
                colour_regions,
                key=lambda item: sum(
                    (row - centre_row) ** 2 + (col - centre_col) ** 2
                    for row, col in item[1]
                ) / len(item[1]),
            )
            selected.extend(closest[1])

    for row, col in selected:
        output[row][col] = 8
    return output
