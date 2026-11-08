"""Visible-example solver for the rail transfer task."""
from __future__ import annotations


def _vertical_runs(grid):
    """Return maximal vertical runs whose cells are colors 8 or 9."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    runs = []
    for column in range(width):
        row = 0
        while row < height:
            if grid[row][column] not in (8, 9):
                row += 1
                continue
            start = row
            values = []
            while row < height and grid[row][column] in (8, 9):
                values.append(grid[row][column])
                row += 1
            runs.append((column, list(range(start, row)), values))
    return runs


def solve(grid):
    """Move the end-aligned 9 block to the rail two cells longer, growing by one."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    runs = _vertical_runs(grid)
    sources = [run for run in runs if 9 in run[2]]
    if len(sources) != 1:
        raise ValueError(f"expected one mixed source rail, found {len(sources)}")

    source_column, source_rows, source_values = sources[0]
    source_length = len(source_rows)
    targets = [
        run
        for run in runs
        if len(run[1]) == source_length + 2 and all(value == 8 for value in run[2])
    ]
    if len(targets) != 1:
        raise ValueError(f"expected one target rail, found {len(targets)}")

    nine_rows = [
        row for row, value in zip(source_rows, source_values) if value == 9
    ]
    if not nine_rows:
        raise ValueError("source rail has no color-9 block")
    at_top = source_values[0] == 9
    block_length = len(nine_rows) + 1

    output = [list(row) for row in grid]
    for row in nine_rows:
        output[row][source_column] = 8

    target_column, target_rows, _ = targets[0]
    paint_rows = target_rows[:block_length] if at_top else target_rows[-block_length:]
    for row in paint_rows:
        output[row][target_column] = 9
    return output
