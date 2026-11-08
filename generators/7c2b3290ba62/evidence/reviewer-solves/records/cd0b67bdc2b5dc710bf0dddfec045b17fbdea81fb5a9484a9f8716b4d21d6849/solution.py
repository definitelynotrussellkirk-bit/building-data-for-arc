def solve(grid):
    """Mark panels whose occupied cells are contained in the reference panel.

    Columns filled with 9 separate equal-height panels.  The second panel is
    the reference mask; the first panel is a worked subset and is not emitted.
    For every panel from the third onward, emit 8 when every non-background
    cell occupies a coordinate present in the reference mask, otherwise 0.
    Colors are labels only; containment is coordinate-based.
    """
    if not grid or not grid[0]:
        return [[]]

    height = len(grid)
    width = len(grid[0])
    separators = [
        column
        for column in range(width)
        if all(grid[row][column] == 9 for row in range(height))
    ]
    boundaries = [-1, *separators, width]

    panels = []
    for left, right in zip(boundaries, boundaries[1:]):
        occupied = {
            (row, column - left - 1)
            for row in range(height)
            for column in range(left + 1, right)
            if grid[row][column] not in (0, 9)
        }
        panels.append(occupied)

    if len(panels) < 3:
        return [[]]

    reference = panels[1]
    return [[8 if panel <= reference else 0 for panel in panels[2:]]]
