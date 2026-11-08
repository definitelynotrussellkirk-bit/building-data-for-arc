def solve(grid):
    """List non-background colors by decreasing occupied height."""
    rows_by_color = {}
    for row_index, row in enumerate(grid):
        for color in row:
            if color != 0:
                rows_by_color.setdefault(color, set()).add(row_index)

    ordered_colors = sorted(
        rows_by_color,
        key=lambda color: -len(rows_by_color[color]),
    )
    return [ordered_colors]
