"""Visible-example hypothesis: join horizontal blue 1-0-1-0-1 triples."""


def solve(grid):
    result = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c in range(len(row) - 4):
            if list(row[c:c + 5]) == [1, 0, 1, 0, 1]:
                result[r][c + 1] = 1
                result[r][c + 3] = 1
    return result
