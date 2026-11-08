from collections import Counter


def _unique_mode(values):
    counts = Counter(values)
    maximum = max(counts.values())
    winners = [color for color, count in counts.items() if count == maximum]
    if len(winners) != 1:
        raise ValueError(f"expected a unique regional mode, got {sorted(winners)}")
    return winners[0]


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    divider_rows = [row for row in range(height) if len(set(grid[row])) == 1]
    divider_cols = [
        col
        for col in range(width)
        if len({grid[row][col] for row in range(height)}) == 1
    ]
    if not divider_rows or not divider_cols:
        raise ValueError("no uniform divider row/column")

    divider_row = divider_rows[0]
    divider_col = divider_cols[0]
    divider = grid[divider_row][divider_col]
    bounds = (
        (1, divider_row, 1, divider_col),
        (1, divider_row, divider_col + 1, width),
        (divider_row + 1, height, 1, divider_col),
        (divider_row + 1, height, divider_col + 1, width),
    )
    modes = []
    for row1, row2, col1, col2 in bounds:
        values = [
            grid[row][col]
            for row in range(row1, row2)
            for col in range(col1, col2)
        ]
        modes.append(_unique_mode(values))

    return [
        [modes[0], divider, modes[1]],
        [divider, divider, divider],
        [modes[2], divider, modes[3]],
    ]
