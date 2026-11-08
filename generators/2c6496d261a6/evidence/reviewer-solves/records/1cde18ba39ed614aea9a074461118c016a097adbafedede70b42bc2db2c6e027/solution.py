from collections import defaultdict


def solve(grid):
    """Keep each non-background color only when all of its cells share one row."""
    rows_by_color = defaultdict(set)
    for r, row in enumerate(grid):
        for value in row:
            if value != 0:
                rows_by_color[value].add(r)

    keep = {value for value, rows in rows_by_color.items() if len(rows) == 1}
    return [
        [value if value == 0 or value in keep else 0 for value in row]
        for row in grid
    ]
