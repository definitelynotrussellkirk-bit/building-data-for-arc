from __future__ import annotations


def _nonseparator_bands(grid: list[list[int]], *, axis: int) -> list[tuple[int, int]]:
    """Return half-open runs between all-zero separator rows or columns."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    length = height if axis == 0 else width

    def is_separator(index: int) -> bool:
        if axis == 0:
            return all(value == 0 for value in grid[index])
        return all(grid[row][index] == 0 for row in range(height))

    bands: list[tuple[int, int]] = []
    start: int | None = None
    for index in range(length + 1):
        separator = index == length or is_separator(index)
        if separator:
            if start is not None:
                bands.append((start, index))
                start = None
        elif start is None:
            start = index
    return bands


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Highlight copies of the marked tile and the straight corridors between them."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    row_bands = _nonseparator_bands(grid, axis=0)
    col_bands = _nonseparator_bands(grid, axis=1)
    result = [row[:] for row in grid]

    marker_position: tuple[int, int] | None = None
    marker_mask: tuple[tuple[bool, ...], ...] | None = None

    for block_row, (row_start, row_end) in enumerate(row_bands):
        for block_col, (col_start, col_end) in enumerate(col_bands):
            block = [row[col_start:col_end] for row in grid[row_start:row_end]]
            if any(value == 8 for row in block for value in row):
                marker_position = (block_row, block_col)
                marker_mask = tuple(
                    tuple(value != 0 for value in row)
                    for row in block
                )
                break
        if marker_position is not None:
            break

    if marker_position is None or marker_mask is None:
        return result

    target_positions: set[tuple[int, int]] = {marker_position}
    for block_row, (row_start, row_end) in enumerate(row_bands):
        for block_col, (col_start, col_end) in enumerate(col_bands):
            if (block_row, block_col) == marker_position:
                continue
            block_mask = tuple(
                tuple(grid[row][col] != 0 for col in range(col_start, col_end))
                for row in range(row_start, row_end)
            )
            if block_mask == marker_mask:
                target_positions.add((block_row, block_col))

    corridor_positions: set[tuple[int, int]] = set()
    for block_row in range(len(row_bands)):
        columns = sorted(
            block_col
            for row_index, block_col in target_positions
            if row_index == block_row
        )
        if len(columns) >= 2:
            for block_col in range(columns[0] + 1, columns[-1]):
                if (block_row, block_col) not in target_positions:
                    corridor_positions.add((block_row, block_col))

    for block_col in range(len(col_bands)):
        rows = sorted(
            block_row
            for block_row, col_index in target_positions
            if col_index == block_col
        )
        if len(rows) >= 2:
            for block_row in range(rows[0] + 1, rows[-1]):
                if (block_row, block_col) not in target_positions:
                    corridor_positions.add((block_row, block_col))

    for block_row, block_col in corridor_positions:
        row_start, row_end = row_bands[block_row]
        col_start, col_end = col_bands[block_col]
        for row in range(row_start, row_end):
            for col in range(col_start, col_end):
                if grid[row][col] == 1:
                    result[row][col] = 7

    for block_row, block_col in target_positions:
        row_start, row_end = row_bands[block_row]
        col_start, col_end = col_bands[block_col]
        for row in range(row_start, row_end):
            for col in range(col_start, col_end):
                if grid[row][col] != 0:
                    result[row][col] = 8

    return result
