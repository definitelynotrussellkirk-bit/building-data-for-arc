"""Visible-example solution for blind task 1ea6c72cb7e3.

Every non-background, non-wall cell is a colored emitter.  It projects in the
four orthogonal directions until the grid edge or a gray (5) wall.  Emitters do
not block one another.  Original nonzero cells are preserved; a formerly empty
cell reached by one emitter takes that emitter's color, while a cell reached by
multiple emitters becomes 8.
"""


def solve(grid):
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    emitters = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 5)
    ]

    # Track emitter identities rather than only colors: the visible task uses
    # unique colors, and overlap is a property of distinct projected crosses.
    hits = [[[] for _ in range(width)] for _ in range(height)]
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    for emitter_id, (start_row, start_col, color) in enumerate(emitters):
        for delta_row, delta_col in directions:
            row = start_row + delta_row
            col = start_col + delta_col
            while 0 <= row < height and 0 <= col < width:
                if grid[row][col] == 5:
                    break
                if grid[row][col] == 0:
                    hits[row][col].append((emitter_id, color))
                row += delta_row
                col += delta_col

    output = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0 or not hits[row][col]:
                continue
            output[row][col] = hits[row][col][0][1] if len(hits[row][col]) == 1 else 8
    return output
