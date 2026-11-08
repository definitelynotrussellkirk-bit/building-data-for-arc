"""Visible-example solution. No generator or reference imports."""


def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("Expected a nonempty rectangular grid")
    result = [list(row) for row in grid]
    for r, row in enumerate(grid):
        green = [c for c, value in enumerate(row) if value == 3]
        if not green:
            continue
        start, length = green[0], len(green)
        if green != list(range(start, start + length)):
            raise ValueError("Expected one contiguous green block per active row")
        destination = 0
        for c in range(start):
            if row[c] == 8:
                destination = c + 1
        for c in green:
            result[r][c] = 0
        for c in range(destination, destination + length):
            result[r][c] = 3
    return result
