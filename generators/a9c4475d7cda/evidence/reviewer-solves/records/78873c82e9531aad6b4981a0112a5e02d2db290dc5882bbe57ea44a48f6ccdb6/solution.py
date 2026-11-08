from __future__ import annotations


def _runs(indices: list[int], limit: int) -> list[list[int]]:
    """Return non-separator index runs between the supplied separators."""
    separators = set(indices)
    runs: list[list[int]] = []
    current: list[int] = []
    for index in range(limit):
        if index in separators:
            if current:
                runs.append(current)
                current = []
        else:
            current.append(index)
    if current:
        runs.append(current)
    return runs


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Summarize each divider-delimited cell by whether it has >=2 markers."""
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    # The divider is the non-background color that occupies complete rows and
    # complete columns. Infer it instead of relying on the examples' color 8.
    full_row_colors = {
        row[0]
        for row in grid
        if row and row[0] != 0 and all(value == row[0] for value in row)
    }
    full_col_colors = {
        grid[0][column]
        for column in range(width)
        if grid[0][column] != 0
        and all(grid[row][column] == grid[0][column] for row in range(height))
    }
    candidates = full_row_colors & full_col_colors
    if len(candidates) != 1:
        raise ValueError(f"expected one divider color, found {sorted(candidates)}")
    divider = next(iter(candidates))

    separator_rows = [
        row for row in range(height) if all(value == divider for value in grid[row])
    ]
    separator_columns = [
        column
        for column in range(width)
        if all(grid[row][column] == divider for row in range(height))
    ]
    row_bands = _runs(separator_rows, height)
    column_bands = _runs(separator_columns, width)

    result: list[list[int]] = []
    for rows in row_bands:
        output_row: list[int] = []
        for columns in column_bands:
            marker_count = sum(
                grid[row][column] not in (0, divider)
                for row in rows
                for column in columns
            )
            output_row.append(1 if marker_count >= 2 else 0)
        result.append(output_row)
    return result
