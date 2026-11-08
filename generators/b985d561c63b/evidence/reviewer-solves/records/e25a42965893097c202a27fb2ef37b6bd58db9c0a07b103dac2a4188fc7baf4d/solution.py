from __future__ import annotations


def _components(cells):
    remaining = set(cells)
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        pending = [start]
        component = []
        while pending:
            row, col = pending.pop()
            component.append((row, col))
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    pending.append(neighbor)
        result.append(component)
    return result


def _bbox(cells):
    rows, cols = zip(*cells)
    return min(rows), min(cols), max(rows) + 1, max(cols) + 1


def solve(grid):
    """Stamp the colored source crop into the top-left of each gray region."""
    source = [
        (row, col)
        for row, cells in enumerate(grid)
        for col, value in enumerate(cells)
        if value not in (0, 5)
    ]
    gray = [
        (row, col)
        for row, cells in enumerate(grid)
        for col, value in enumerate(cells)
        if value == 5
    ]
    if not source or not gray:
        return [list(row) for row in grid]

    source_r0, source_c0, source_r1, source_c1 = _bbox(source)
    template = [
        list(row[source_c0:source_c1])
        for row in grid[source_r0:source_r1]
    ]
    result = [list(row) for row in grid]
    for region in _components(gray):
        target_r0, target_c0, target_r1, target_c1 = _bbox(region)
        if target_r1 - target_r0 < len(template):
            continue
        if target_c1 - target_c0 < len(template[0]):
            continue
        for dr, row in enumerate(template):
            for dc, value in enumerate(row):
                result[target_r0 + dr][target_c0 + dc] = value
    return result
