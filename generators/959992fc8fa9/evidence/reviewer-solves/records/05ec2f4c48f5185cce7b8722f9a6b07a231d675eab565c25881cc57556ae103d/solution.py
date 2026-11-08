def solve(grid):
    """Extend each colored marker across its row and column.

    Empty cells stay black unless reached by a marker's row/column.  A cell
    reached by one distinct marker color takes that color; crossings between
    different colors are red (2).  Crossings between equal colors retain that
    color.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0

    row_colors = [set() for _ in range(height)]
    col_colors = [set() for _ in range(width)]
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color != 0:
                row_colors[row].add(color)
                col_colors[col].add(color)

    output = []
    for row in range(height):
        output_row = []
        for col in range(width):
            colors = row_colors[row] | col_colors[col]
            if not colors:
                output_row.append(0)
            elif len(colors) == 1:
                output_row.append(next(iter(colors)))
            else:
                output_row.append(2)
        output.append(output_row)
    return output
