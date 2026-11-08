def solve(grid):
    """Compare each pair of non-background colors by occupied cell count."""
    counts = {}
    for row in grid:
        for value in row:
            if value != 0:
                counts[value] = counts.get(value, 0) + 1

    colors = sorted(counts)
    result = []
    for row_color in colors:
        row = []
        for column_color in colors:
            if row_color == column_color:
                row.append(0)
            elif counts[row_color] > counts[column_color]:
                row.append(row_color)
            elif counts[column_color] > counts[row_color]:
                row.append(column_color)
            else:
                row.append(0)
        result.append(row)
    return result
