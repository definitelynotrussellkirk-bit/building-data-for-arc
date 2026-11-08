"""Visible-example solution for task c8138b7e476c."""


def solve(grid):
    """Mirror the rows above the solid-9 separator into the rows below it."""
    out = [list(row) for row in grid]
    separator = next(
        i for i, row in enumerate(out)
        if row and all(cell == 9 for cell in row)
    )
    for offset, source_row in enumerate(reversed(out[:separator]), start=1):
        target = separator + offset
        if target < len(out):
            out[target] = list(source_row)
    return out
