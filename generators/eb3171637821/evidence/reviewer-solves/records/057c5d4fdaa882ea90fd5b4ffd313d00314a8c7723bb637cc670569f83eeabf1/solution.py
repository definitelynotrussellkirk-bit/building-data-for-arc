"""Collapse a lattice of monochrome panels to one pixel per panel."""


def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("Expected a nonempty rectangular grid")
    height, width = len(grid), len(grid[0])
    colors = {value for row in grid for value in row}
    candidates = []
    for color in colors:
        rows = [all(value == color for value in row) for row in grid]
        cols = [all(grid[r][c] == color for r in range(height)) for c in range(width)]
        if any(rows) and any(cols):
            candidates.append((sum(rows) + sum(cols), color, rows, cols))
    if not candidates:
        raise ValueError("No full-row/full-column lattice found")
    _, _, separator_rows, separator_cols = max(candidates)

    def starts(separators):
        return [i for i, marked in enumerate(separators)
                if not marked and (i == 0 or separators[i - 1])]

    return [[grid[r][c] for c in starts(separator_cols)]
            for r in starts(separator_rows)]
