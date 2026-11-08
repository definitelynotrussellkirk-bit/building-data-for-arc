def solve(grid):
    """Collapse each consecutive band of identical rows and columns."""
    if not grid:
        return []

    rows = []
    for row in grid:
        if not rows or row != rows[-1]:
            rows.append(list(row))

    keep_columns = [0]
    for column in range(1, len(rows[0])):
        previous = [row[column - 1] for row in rows]
        current = [row[column] for row in rows]
        if current != previous:
            keep_columns.append(column)

    return [[row[column] for column in keep_columns] for row in rows]
