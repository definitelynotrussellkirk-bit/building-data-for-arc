"""Visible-example solution for task 42f19ef6d600."""


def _components(grid, background):
    """Yield same-color 4-connected components as lists of (row, column)."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == background or (row, column) in seen:
                continue

            component = []
            stack = [(row, column)]
            seen.add((row, column))
            while stack:
                current_row, current_column = stack.pop()
                component.append((current_row, current_column))
                for row_step, column_step in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor_row = current_row + row_step
                    neighbor_column = current_column + column_step
                    if not (0 <= neighbor_row < height and 0 <= neighbor_column < width):
                        continue
                    neighbor = (neighbor_row, neighbor_column)
                    if neighbor in seen:
                        continue
                    if grid[neighbor_row][neighbor_column] != color:
                        continue
                    seen.add(neighbor)
                    stack.append(neighbor)

            yield component


def _runs(values):
    """Yield inclusive endpoints of consecutive integer runs."""
    ordered = sorted(values)
    if not ordered:
        return

    start = previous = ordered[0]
    for value in ordered[1:]:
        if value == previous + 1:
            previous = value
            continue
        yield start, previous
        start = previous = value
    yield start, previous


def solve(grid):
    """Extend every length-2+ row/column stroke of each 2-D object in blue.

    The visible examples use orange (7) as background and blue (2) for the
    one-cell extensions.  A purely horizontal or vertical component is a
    distractor and remains unchanged.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    background = 7
    extension_color = 2
    height = len(grid)
    width = len(grid[0])
    result = [row[:] for row in grid]

    for component in _components(grid, background):
        rows = [row for row, _ in component]
        columns = [column for _, column in component]

        # The long one-cell-thick bar in the visible examples is deliberately
        # not extended; only components spanning both axes participate.
        if min(rows) == max(rows) or min(columns) == max(columns):
            continue

        columns_by_row = {}
        rows_by_column = {}
        for row, column in component:
            columns_by_row.setdefault(row, []).append(column)
            rows_by_column.setdefault(column, []).append(row)

        for row, row_columns in columns_by_row.items():
            for start, end in _runs(row_columns):
                if end - start + 1 < 2:
                    continue
                for column in (start - 1, end + 1):
                    if 0 <= column < width and grid[row][column] == background:
                        result[row][column] = extension_color

        for column, column_rows in rows_by_column.items():
            for start, end in _runs(column_rows):
                if end - start + 1 < 2:
                    continue
                for row in (start - 1, end + 1):
                    if 0 <= row < height and grid[row][column] == background:
                        result[row][column] = extension_color

    return result
