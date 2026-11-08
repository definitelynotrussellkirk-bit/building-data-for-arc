"""Visible-example solution for blind task ebe910be6876."""


def solve(grid):
    """Expand each colored marker's 2x2 lattice cell into a 4x4 block.

    The output canvas is twice the input height and width.  Input rows and
    columns occur in two-cell macro-cells (a zero separator followed by the
    marker position); a marker anywhere in a macro-cell colors the
    corresponding 4x4 output macro-cell.  A trailing unpaired input row or
    column remains background after doubling.
    """
    if not grid:
        return []
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    height = len(grid)
    output = [[0 for _ in range(2 * width)] for _ in range(2 * height)]

    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color == 0:
                continue
            out_row = (row_index // 2) * 4
            out_column = (column_index // 2) * 4
            for r in range(out_row, min(out_row + 4, 2 * height)):
                for c in range(out_column, min(out_column + 4, 2 * width)):
                    output[r][c] = color

    return output
