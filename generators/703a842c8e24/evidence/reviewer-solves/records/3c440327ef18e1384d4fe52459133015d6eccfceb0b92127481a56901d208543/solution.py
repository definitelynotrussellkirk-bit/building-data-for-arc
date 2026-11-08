from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Keep each row header and shift that row's body right by the header."""
    output: list[list[int]] = []
    for row in grid:
        header = row[0]
        body = row[1:]
        shifted = body[-header:] + body[:-header]
        output.append([header, *shifted])
    return output
