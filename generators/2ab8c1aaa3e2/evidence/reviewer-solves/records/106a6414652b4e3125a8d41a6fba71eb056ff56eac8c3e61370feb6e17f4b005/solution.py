"""Visible-example solution: join exactly two equal markers within each column."""


def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected a nonempty rectangular grid')
    answer = [list(row) for row in grid]
    for column in range(len(grid[0])):
        occurrences = {}
        for row in range(len(grid)):
            value = grid[row][column]
            if value:
                occurrences.setdefault(value, []).append(row)
        for value, rows in occurrences.items():
            if len(rows) != 2:
                continue
            for row in range(rows[0], rows[1] + 1):
                answer[row][column] = value
    return answer
