def solve(grid):
    """Pack all occupied row cells around the 6, retaining side counts."""
    result = [[7 for _ in row] for row in grid]
    for r, row in enumerate(grid):
        anchors = [c for c, value in enumerate(row) if value == 6]
        if not anchors:
            continue
        if len(anchors) != 1:
            raise ValueError("Visible examples support exactly one 6 per active row")
        anchor = anchors[0]
        left_count = sum(value != 7 for value in row[:anchor])
        right_count = sum(value != 7 for value in row[anchor + 1:])
        for c in range(anchor - left_count, anchor + right_count + 1):
            result[r][c] = 8
    return result
