"""Visible-example solution for the 2x3 panel Boolean analogy puzzle."""


def _mask(panel):
    return [[cell != 0 for cell in row] for row in panel]


def _apply(left, right, operation):
    if operation == "and":
        return [[a and b for a, b in zip(arow, brow)] for arow, brow in zip(left, right)]
    if operation == "xor":
        return [[a != b for a, b in zip(arow, brow)] for arow, brow in zip(left, right)]
    if operation == "or":
        return [[a or b for a, b in zip(arow, brow)] for arow, brow in zip(left, right)]
    if operation == "left-minus-right":
        return [[a and not b for a, b in zip(arow, brow)] for arow, brow in zip(left, right)]
    if operation == "right-minus-left":
        return [[b and not a for a, b in zip(arow, brow)] for arow, brow in zip(left, right)]
    raise ValueError(f"unknown operation: {operation}")


def solve(grid):
    """Infer the top-row Boolean operation and apply it to the bottom row."""
    result = [row[:] for row in grid]

    top_left = _mask([row[0:4] for row in grid[0:4]])
    top_middle = _mask([row[5:9] for row in grid[0:4]])
    top_result = _mask([row[10:14] for row in grid[0:4]])

    operation = None
    for candidate in ("and", "xor", "or", "left-minus-right", "right-minus-left"):
        if _apply(top_left, top_middle, candidate) == top_result:
            operation = candidate
            break
    if operation is None:
        raise ValueError("top-right panel does not match a supported Boolean operation")

    bottom_left = _mask([row[0:4] for row in grid[5:9]])
    bottom_middle = _mask([row[5:9] for row in grid[5:9]])
    bottom_result = _apply(bottom_left, bottom_middle, operation)

    for row_index, row in enumerate(bottom_result, start=5):
        for column_offset, filled in enumerate(row):
            result[row_index][10 + column_offset] = 2 if filled else 0
    return result
