from __future__ import annotations


def _panel_ranges(grid: list[list[int]]) -> list[tuple[int, int]]:
    """Return half-open column ranges separated by full-height color-5 bars."""
    if not grid or not grid[0]:
        return []
    width = len(grid[0])
    separators = [
        col for col in range(width) if all(row[col] == 5 for row in grid)
    ]
    ranges: list[tuple[int, int]] = []
    start = 0
    for col in separators:
        if start < col:
            ranges.append((start, col))
        start = col + 1
    if start < width:
        ranges.append((start, width))
    return ranges


def _top_left_nonzero(panel: list[list[int]]) -> tuple[int, int]:
    cells = [
        (row_index, col_index)
        for row_index, row in enumerate(panel)
        for col_index, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        raise ValueError("expected a non-empty object panel")
    return min(row for row, _ in cells), min(col for _, col in cells)


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Transfer the middle panel's added marks to the third panel's object.

    The first and middle panels share a base object.  The middle panel adds
    marks to it.  The third panel contains a target object.  Translate the
    added marks by the offset between the source and target objects' bounding
    box top-left corners, then overlay them on a copy of the target panel.
    """
    if not grid or not grid[0]:
        return []
    if any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be rectangular")

    ranges = _panel_ranges(grid)
    if len(ranges) != 3:
        raise ValueError(f"expected three panels, found {len(ranges)}")

    panels = [
        [row[start:end] for row in grid]
        for start, end in ranges
    ]
    source, marked, target = panels
    if not (len(source[0]) == len(marked[0]) == len(target[0])):
        raise ValueError("expected equal-width panels")

    source_top, source_left = _top_left_nonzero(source)
    target_top, target_left = _top_left_nonzero(target)
    row_shift = target_top - source_top
    col_shift = target_left - source_left

    output = [row[:] for row in target]
    for row_index, row in enumerate(marked):
        for col_index, value in enumerate(row):
            if value == source[row_index][col_index] or value == 0:
                continue
            out_row = row_index + row_shift
            out_col = col_index + col_shift
            if 0 <= out_row < len(output) and 0 <= out_col < len(output[0]):
                output[out_row][out_col] = value

    return output
