"""Visible-example solution for the blind ARC episode.

The rows above the all-9 divider form a legend.  All-9 columns split that
legend into templates; each template's nonzero color identifies the template.
Every matching colored cell below the divider is the center anchor where that
template is stamped.
"""


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]
    if not height or not width:
        return result

    divider_rows = [
        r for r, row in enumerate(grid)
        if len(row) == width and all(value == 9 for value in row)
    ]
    if not divider_rows:
        return result
    divider = divider_rows[0]
    if divider == 0:
        return result

    separator_columns = {
        c for c in range(width)
        if all(grid[r][c] == 9 for r in range(divider))
    }

    column_runs = []
    start = None
    for c in range(width + 1):
        is_template_column = c < width and c not in separator_columns
        if is_template_column and start is None:
            start = c
        elif not is_template_column and start is not None:
            column_runs.append((start, c))
            start = None

    templates = {}
    anchor_row = divider // 2
    for left, right in column_runs:
        block_width = right - left
        anchor_col = block_width // 2
        colors = {
            grid[r][c]
            for r in range(divider)
            for c in range(left, right)
            if grid[r][c] not in (0, 9)
        }
        if len(colors) != 1:
            continue
        color = next(iter(colors))
        offsets = []
        for r in range(divider):
            for c in range(left, right):
                if grid[r][c] == color:
                    offsets.append((r - anchor_row, c - left - anchor_col))
        templates[color] = offsets

    # Snapshot the anchors before drawing so newly stamped pixels do not become
    # additional anchors during the same pass.
    anchors = [
        (r, c, grid[r][c])
        for r in range(divider + 1, height)
        for c in range(width)
        if grid[r][c] in templates
    ]

    for row, col, color in anchors:
        for dr, dc in templates[color]:
            rr, cc = row + dr, col + dc
            if 0 <= rr < height and 0 <= cc < width:
                result[rr][cc] = color

    return result
