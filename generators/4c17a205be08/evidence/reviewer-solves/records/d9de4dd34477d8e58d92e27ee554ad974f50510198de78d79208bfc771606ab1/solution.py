from __future__ import annotations


def _split_panels(grid: list[list[int]]) -> list[list[list[int]]]:
    """Split a row-aligned grid at columns consisting entirely of separator 9s."""
    separator_columns = {
        column
        for column in range(len(grid[0]))
        if all(row[column] == 9 for row in grid)
    }
    panels: list[list[list[int]]] = []
    start = 0
    for column in range(len(grid[0]) + 1):
        if column == len(grid[0]) or column in separator_columns:
            if start < column:
                panels.append([row[start:column] for row in grid])
            start = column + 1
    if len(panels) != 3:
        raise ValueError(f"expected three panels, found {len(panels)}")
    return panels


def _crop_object(panel: list[list[int]]) -> list[list[int]]:
    """Return the smallest rectangle containing every non-background cell."""
    occupied = [
        (row, column)
        for row, values in enumerate(panel)
        for column, value in enumerate(values)
        if value != 0
    ]
    if not occupied:
        return []
    rows, columns = zip(*occupied)
    top, bottom = min(rows), max(rows)
    left, right = min(columns), max(columns)
    return [values[left : right + 1] for values in panel[top : bottom + 1]]


def _rotate_clockwise(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _transform(
    grid: list[list[int]], quarter_turns_clockwise: int, reflect_left_right: bool
) -> list[list[int]]:
    result = [row[:] for row in grid]
    for _ in range(quarter_turns_clockwise):
        result = _rotate_clockwise(result)
    if reflect_left_right:
        result = [row[::-1] for row in result]
    return result


def solve(grid: list[list[int]]) -> list[list[int]]:
    first, second, payload = (_crop_object(panel) for panel in _split_panels(grid))

    matches: list[tuple[int, bool]] = []
    for turns in range(4):
        for reflected in (False, True):
            if _transform(first, turns, reflected) == second:
                matches.append((turns, reflected))

    if not matches:
        raise ValueError("panel 2 is not a dihedral transform of panel 1")

    candidates = [_transform(payload, turns, reflected) for turns, reflected in matches]
    if any(candidate != candidates[0] for candidate in candidates[1:]):
        raise ValueError("the panel transformation is ambiguous for this payload")
    return candidates[0]
