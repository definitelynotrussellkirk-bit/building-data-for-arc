"""Blind ARC solve: infer the demonstrated Boolean panel operation."""


def solve(grid):
    height = len(grid)
    width = len(grid[0])

    # The puzzle is a 2x3 panel layout separated by solid non-background lines.
    separator_rows = [
        r for r, row in enumerate(grid)
        if row and row[0] != 0 and all(value == row[0] for value in row)
    ]
    separator_cols = [
        c for c in range(width)
        if grid[0][c] != 0 and all(grid[r][c] == grid[0][c] for r in range(height))
    ]
    if len(separator_rows) != 1 or len(separator_cols) != 2:
        raise ValueError("expected one horizontal and two vertical separator lines")

    split_row = separator_rows[0]
    left_split, right_split = separator_cols

    def panel(r0, r1, c0, c1):
        return [row[c0:c1] for row in grid[r0:r1]]

    top_left = panel(0, split_row, 0, left_split)
    top_middle = panel(0, split_row, left_split + 1, right_split)
    top_result = panel(0, split_row, right_split + 1, width)
    bottom_left = panel(split_row + 1, height, 0, left_split)
    bottom_middle = panel(split_row + 1, height, left_split + 1, right_split)

    # Learn the truth table directly from the complete worked example on top.
    truth_table = {}
    result_color = None
    for r in range(len(top_result)):
        for c in range(len(top_result[0])):
            key = (top_left[r][c] != 0, top_middle[r][c] != 0)
            occupied = top_result[r][c] != 0
            previous = truth_table.setdefault(key, occupied)
            if previous != occupied:
                raise ValueError("top panels do not define a consistent cellwise operation")
            if occupied:
                result_color = top_result[r][c]

    if result_color is None:
        # The supplied tasks use color 2 as the result ink. This fallback is only
        # needed for a degenerate all-background demonstration.
        result_color = 2

    answer = [row[:] for row in grid]
    for r in range(len(bottom_left)):
        for c in range(len(bottom_left[0])):
            key = (bottom_left[r][c] != 0, bottom_middle[r][c] != 0)
            if key not in truth_table:
                raise ValueError(f"demonstration omitted truth-table case {key}")
            answer[split_row + 1 + r][right_split + 1 + c] = (
                result_color if truth_table[key] else 0
            )
    return answer
