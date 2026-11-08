from __future__ import annotations


def _axis_candidates(grid: list[list[int]]) -> list[tuple[str, int, int, int]]:
    """Return (orientation, fixed_coordinate, span_start, span_end) axes."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    axes: list[tuple[str, int, int, int]] = []

    for row in range(height):
        col = 0
        while col < width:
            while col < width and grid[row][col] == 0:
                col += 1
            start = col
            while col < width and grid[row][col] != 0:
                col += 1
            end = col - 1
            if start <= end:
                length = end - start + 1
                fours = sum(grid[row][c] == 4 for c in range(start, end + 1))
                if length >= 3 and fours >= 3 and 5 * fours >= 3 * length:
                    axes.append(("h", row, start, end))

    for col in range(width):
        row = 0
        while row < height:
            while row < height and grid[row][col] == 0:
                row += 1
            start = row
            while row < height and grid[row][col] != 0:
                row += 1
            end = row - 1
            if start <= end:
                length = end - start + 1
                fours = sum(grid[r][col] == 4 for r in range(start, end + 1))
                if length >= 3 and fours >= 3 and 5 * fours >= 3 * length:
                    axes.append(("v", col, start, end))

    return axes


def _distance_to_axis(row: int, col: int, axis: tuple[str, int, int, int]) -> int:
    orientation, fixed, start, end = axis
    if orientation == "h":
        along = start - col if col < start else col - end if col > end else 0
        return abs(row - fixed) + along
    along = start - row if row < start else row - end if row > end else 0
    return abs(col - fixed) + along


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]
    axes = _axis_candidates(grid)
    if not axes:
        return result

    groups: list[list[tuple[int, int, int]]] = [[] for _ in axes]
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == 0:
                continue
            axis_index = min(
                range(len(axes)),
                key=lambda index: (_distance_to_axis(row, col, axes[index]), index),
            )
            groups[axis_index].append((row, col, value))

    for axis, cells in zip(axes, groups):
        orientation, fixed, _, _ = axis
        if orientation == "h":
            negative = [(r, c, v) for r, c, v in cells if r < fixed]
            positive = [(r, c, v) for r, c, v in cells if r > fixed]
            source, target = (negative, positive) if len(negative) >= len(positive) else (positive, negative)
            for row, col, _ in target:
                result[row][col] = 0
            for row, col, value in source:
                reflected_row = 2 * fixed - row
                if 0 <= reflected_row < height:
                    result[reflected_row][col] = value
        else:
            negative = [(r, c, v) for r, c, v in cells if c < fixed]
            positive = [(r, c, v) for r, c, v in cells if c > fixed]
            source, target = (negative, positive) if len(negative) >= len(positive) else (positive, negative)
            for row, col, _ in target:
                result[row][col] = 0
            for row, col, value in source:
                reflected_col = 2 * fixed - col
                if 0 <= reflected_col < width:
                    result[row][reflected_col] = value

    return result
