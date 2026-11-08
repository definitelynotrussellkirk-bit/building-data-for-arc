"""Visible-example-only solution for the blind ARC episode."""

from __future__ import annotations


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    """Return 4-connected non-background components, ignoring their colors."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            component: list[tuple[int, int]] = []
            while stack:
                cur_row, cur_col = stack.pop()
                component.append((cur_row, cur_col))
                for d_row, d_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt_row = cur_row + d_row
                    nxt_col = cur_col + d_col
                    if not (0 <= nxt_row < height and 0 <= nxt_col < width):
                        continue
                    point = (nxt_row, nxt_col)
                    if point in seen or grid[nxt_row][nxt_col] == 0:
                        continue
                    seen.add(point)
                    stack.append(point)
            components.append(component)
    return components


def _minimum_squared_distance(
    first: list[tuple[int, int]], second: list[tuple[int, int]]
) -> int:
    return min(
        (row_a - row_b) ** 2 + (col_a - col_b) ** 2
        for row_a, col_a in first
        for row_b, col_b in second
    )


def _runs(values: list[int]) -> list[tuple[int, int, int]]:
    """Return (start, stop-exclusive, value) runs."""
    if not values:
        return []
    answer: list[tuple[int, int, int]] = []
    start = 0
    value = values[0]
    for index in range(1, len(values)):
        if values[index] == value:
            continue
        answer.append((start, index, value))
        start = index
        value = values[index]
    answer.append((start, len(values), value))
    return answer


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Select a marker-indexed color run from each line of the main pattern.

    The largest nonzero component is treated as the striped pattern.  The nearest
    detached component is the marker.  Its area is the number of color-boundary
    crossings to make from the nearer end of the pattern's long axis.  The cells
    in the resulting run are painted azure (8); everything else is erased.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]
    if height == 0 or width == 0:
        return output

    components = _components(grid)
    if len(components) < 2:
        return output

    # The examples distinguish one large multicolor pattern from detached cues.
    main_index = max(range(len(components)), key=lambda index: len(components[index]))
    main = components[main_index]
    detached = [
        component for index, component in enumerate(components) if index != main_index
    ]
    marker = min(
        detached,
        key=lambda component: (
            _minimum_squared_distance(main, component),
            -len(component),
            min(component),
        ),
    )
    crossing_count = len(marker)

    rows = [row for row, _ in main]
    cols = [col for _, col in main]
    top, bottom = min(rows), max(rows)
    left, right = min(cols), max(cols)
    box_height = bottom - top + 1
    box_width = right - left + 1
    marker_row = sum(row for row, _ in marker) / len(marker)
    marker_col = sum(col for _, col in marker) / len(marker)

    if box_width >= box_height:
        # Work row by row, starting at the horizontal end nearer the marker.
        reverse = abs(marker_col - right) < abs(marker_col - left)
        for row in range(top, bottom + 1):
            values = grid[row][left : right + 1]
            if reverse:
                values = list(reversed(values))
            runs = _runs(values)
            if crossing_count >= len(runs):
                continue
            start, stop, value = runs[crossing_count]
            if value == 0:
                continue
            for offset in range(start, stop):
                col = right - offset if reverse else left + offset
                output[row][col] = 8
    else:
        # Work column by column, starting at the vertical end nearer the marker.
        reverse = abs(marker_row - bottom) < abs(marker_row - top)
        for col in range(left, right + 1):
            values = [grid[row][col] for row in range(top, bottom + 1)]
            if reverse:
                values.reverse()
            runs = _runs(values)
            if crossing_count >= len(runs):
                continue
            start, stop, value = runs[crossing_count]
            if value == 0:
                continue
            for offset in range(start, stop):
                row = bottom - offset if reverse else top + offset
                output[row][col] = 8

    return output
