from collections import Counter


def _runs(indices):
    """Return inclusive contiguous runs from an ordered sequence of indices."""
    runs = []
    for index in indices:
        if not runs or index != runs[-1][1] + 1:
            runs.append([index, index])
        else:
            runs[-1][1] = index
    return runs


def solve(grid):
    height = len(grid)
    width = len(grid[0])

    solid_rows = {}
    for row_index, row in enumerate(grid):
        if all(value == row[0] for value in row):
            solid_rows.setdefault(row[0], []).append(row_index)

    solid_cols = {}
    for col_index in range(width):
        value = grid[0][col_index]
        if all(grid[row_index][col_index] == value for row_index in range(height)):
            solid_cols.setdefault(value, []).append(col_index)

    divider_candidates = set(solid_rows) & set(solid_cols)
    if not divider_candidates:
        raise ValueError("no color forms both complete divider rows and columns")

    # The divider color is the one that supplies the strongest two-dimensional
    # lattice of full lines. Valid tasks have a unique winner.
    divider = max(
        divider_candidates,
        key=lambda color: (
            len(solid_rows[color]) * len(solid_cols[color]),
            len(solid_rows[color]) + len(solid_cols[color]),
        ),
    )

    divider_rows = set(solid_rows[divider])
    divider_cols = set(solid_cols[divider])
    row_runs = _runs(i for i in range(height) if i not in divider_rows)
    col_runs = _runs(i for i in range(width) if i not in divider_cols)

    panels = []
    for row_start, row_end in row_runs:
        panel_row = []
        for col_start, col_end in col_runs:
            values = [
                grid[row_index][col_index]
                for row_index in range(row_start, row_end + 1)
                for col_index in range(col_start, col_end + 1)
            ]
            panel_row.append(Counter(values).most_common(1)[0][0])
        panels.append(panel_row[::-1])

    return panels
