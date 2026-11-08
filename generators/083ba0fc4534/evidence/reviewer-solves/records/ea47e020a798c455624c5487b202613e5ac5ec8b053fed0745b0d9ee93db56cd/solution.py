"""Visible-example inference: aligned majority across three separated panels."""


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    if (width - 2) % 3:
        raise ValueError("Expected three equally wide panels and two separators")
    panel_width = (width - 2) // 3
    separators = (panel_width, 2 * panel_width + 1)
    separator_color = grid[0][separators[0]]
    if any(grid[r][c] != separator_color for r in range(height) for c in separators):
        raise ValueError("Panel separators must be full monochrome columns")
    result = []
    for r in range(height):
        row = []
        for c in range(panel_width):
            values = [grid[r][c + k * (panel_width + 1)] for k in range(3)]
            repeated = [v for v in set(values) if v != 0 and values.count(v) >= 2]
            row.append(repeated[0] if repeated else 0)
        result.append(row)
    return result
