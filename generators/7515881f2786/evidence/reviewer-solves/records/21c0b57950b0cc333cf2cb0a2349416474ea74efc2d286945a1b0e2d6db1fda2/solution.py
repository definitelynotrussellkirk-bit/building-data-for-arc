from collections import Counter, defaultdict


def solve(grid):
    """Fill spans between same-colored anchors sharing a row or column.

    Anchor relationships are measured from the original input so newly filled
    cells cannot trigger a cascade of additional lines.
    """
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]
    output = [list(row) for row in grid]

    positions_by_color = defaultdict(list)
    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            if value != background:
                positions_by_color[value].append((row_index, column_index))

    for color, positions in positions_by_color.items():
        columns_by_row = defaultdict(list)
        rows_by_column = defaultdict(list)
        for row_index, column_index in positions:
            columns_by_row[row_index].append(column_index)
            rows_by_column[column_index].append(row_index)

        for row_index, columns in columns_by_row.items():
            if len(columns) >= 2:
                for column_index in range(min(columns), max(columns) + 1):
                    output[row_index][column_index] = color

        for column_index, rows in rows_by_column.items():
            if len(rows) >= 2:
                for row_index in range(min(rows), max(rows) + 1):
                    output[row_index][column_index] = color

    return output
