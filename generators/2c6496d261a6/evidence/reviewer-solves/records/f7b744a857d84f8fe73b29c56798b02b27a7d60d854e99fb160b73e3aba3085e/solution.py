from collections import defaultdict


def solve(grid):
    """Keep non-background colors whose occurrences are confined to one row."""
    rows_by_color = defaultdict(set)
    for row_index, row in enumerate(grid):
        for value in row:
            if value != 0:
                rows_by_color[value].add(row_index)

    keep = {value for value, rows in rows_by_color.items() if len(rows) == 1}
    return [
        [value if value == 0 or value in keep else 0 for value in row]
        for row in grid
    ]
