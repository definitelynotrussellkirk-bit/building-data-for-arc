"""Visible-examples-only solution for blind ARC task 9000d0ea6484."""


def solve(grid):
    """Overlay four separator-delimited panels with priority 3rd > 4th > 1st > 2nd."""
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    separator_columns = {
        column
        for column in range(width)
        if all(grid[row][column] == 3 for row in range(height))
    }

    panels = []
    start = 0
    for column in range(width + 1):
        if column == width or column in separator_columns:
            if start < column:
                panels.append([row[start:column] for row in grid])
            start = column + 1

    if len(panels) != 4:
        raise ValueError(f"expected four panels, found {len(panels)}")
    panel_width = len(panels[0][0])
    if any(len(row) != panel_width for panel in panels for row in panel):
        raise ValueError("panels must have equal widths")

    priority = (2, 3, 0, 1)
    output = []
    for row in range(height):
        output_row = []
        for column in range(panel_width):
            value = 0
            for panel_index in priority:
                candidate = panels[panel_index][row][column]
                if candidate != 0:
                    value = candidate
                    break
            output_row.append(value)
        output.append(output_row)
    return output
