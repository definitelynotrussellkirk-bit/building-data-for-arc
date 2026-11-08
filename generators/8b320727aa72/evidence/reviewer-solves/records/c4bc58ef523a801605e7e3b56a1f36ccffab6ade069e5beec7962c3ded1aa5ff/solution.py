from collections import Counter


def _separator_indices(grid):
    rows = [r for r, row in enumerate(grid) if len(set(row)) == 1]
    cols = [
        c
        for c in range(len(grid[0]))
        if len({grid[r][c] for r in range(len(grid))}) == 1
    ]
    # In the visible examples, separator rows and columns share the same color
    # and partition the input into equal-sized square tiles.
    candidates = []
    for color in set(grid[r][0] for r in rows):
        matching_rows = [r for r in rows if grid[r][0] == color]
        matching_cols = [c for c in cols if grid[0][c] == color]
        if matching_rows and matching_cols:
            candidates.append((len(matching_rows) + len(matching_cols), matching_rows, matching_cols))
    if not candidates:
        raise ValueError("could not identify separator rows and columns")
    _, separator_rows, separator_cols = max(candidates)
    return separator_rows, separator_cols


def _segments(length, separators):
    separators = set(separators)
    segments = []
    start = 0
    while start < length:
        while start < length and start in separators:
            start += 1
        if start >= length:
            break
        end = start
        while end < length and end not in separators:
            end += 1
        segments.append(list(range(start, end)))
        start = end
    return segments


def solve(grid):
    separator_rows, separator_cols = _separator_indices(grid)
    row_blocks = _segments(len(grid), separator_rows)
    col_blocks = _segments(len(grid[0]), separator_cols)
    if not row_blocks or not col_blocks:
        raise ValueError("input has no tile blocks")
    tile_h = len(row_blocks[0])
    tile_w = len(col_blocks[0])
    if any(len(block) != tile_h for block in row_blocks) or any(
        len(block) != tile_w for block in col_blocks
    ):
        raise ValueError("tile blocks are not uniform")

    output = []
    for local_r in range(tile_h):
        out_row = []
        for local_c in range(tile_w):
            values = [
                grid[row_block[local_r]][col_block[local_c]]
                for row_block in row_blocks
                for col_block in col_blocks
            ]
            unique = set(values)
            if len(unique) == 1:
                out_row.append(values[0])
            else:
                # Visible examples consistently use 1 to mark any coordinate
                # where the repeated tiles disagree.
                out_row.append(1)
        output.append(out_row)
    return output
