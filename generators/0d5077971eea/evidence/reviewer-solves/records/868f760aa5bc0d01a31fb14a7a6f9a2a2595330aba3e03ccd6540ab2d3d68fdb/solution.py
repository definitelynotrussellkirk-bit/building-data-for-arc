"""Attempted solution checked using the three visible demonstration pairs."""


def solve(grid):
    result = []
    for row in grid:
        header = row[0]
        result.append([
            header if col > 0 and value == 8 and header != 0 else value
            for col, value in enumerate(row)
        ])
    return result
