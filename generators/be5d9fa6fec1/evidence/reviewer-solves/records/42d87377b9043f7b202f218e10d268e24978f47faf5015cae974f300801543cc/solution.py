def solve(grid):
    """Recolor every third horizontal row-run, starting with the first."""
    result = [row[:] for row in grid]
    if not grid:
        return result

    run_start = 0
    run_index = 0
    for row_index in range(1, len(grid) + 1):
        if row_index < len(grid) and grid[row_index] == grid[run_start]:
            continue

        if run_index % 3 == 0:
            for r in range(run_start, row_index):
                result[r] = [2 if value != 0 else 0 for value in grid[r]]

        run_start = row_index
        run_index += 1

    return result
