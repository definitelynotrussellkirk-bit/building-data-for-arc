"""Visible-example solution for the reviewer-authored ARC episode.

The examples distinguish two counting conventions:
* green (3): count maximal horizontal runs;
* red (2): count 4-connected components.
Write that many 3s followed by that many 2s into a 2x3 row-major tally,
padding with zero and clipping after six cells.
"""

from collections import deque


def _validate_grid(grid):
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) and row for row in grid):
        raise ValueError("grid must be a non-empty rectangular list of rows")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")


def _horizontal_runs(grid, color):
    return sum(
        1
        for row in grid
        for column, value in enumerate(row)
        if value == color and (column == 0 or row[column - 1] != color)
    )


def _components(grid, color):
    height, width = len(grid), len(grid[0])
    seen = set()
    count = 0
    for row in range(height):
        for column in range(width):
            if grid[row][column] != color or (row, column) in seen:
                continue
            count += 1
            seen.add((row, column))
            queue = deque([(row, column)])
            while queue:
                current_row, current_column = queue.popleft()
                for next_row, next_column in (
                    (current_row - 1, current_column),
                    (current_row + 1, current_column),
                    (current_row, current_column - 1),
                    (current_row, current_column + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_column < width):
                        continue
                    point = (next_row, next_column)
                    if point in seen or grid[next_row][next_column] != color:
                        continue
                    seen.add(point)
                    queue.append(point)
    return count


def solve(grid):
    _validate_grid(grid)
    green_count = _horizontal_runs(grid, 3)
    red_count = _components(grid, 2)
    tally = ([3] * green_count + [2] * red_count + [0] * 6)[:6]
    return [tally[:3], tally[3:]]
