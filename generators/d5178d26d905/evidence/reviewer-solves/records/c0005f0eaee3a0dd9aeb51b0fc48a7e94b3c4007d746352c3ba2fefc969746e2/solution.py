def _solve_vertical(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0

    divider_columns = [
        col for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    if not divider_columns:
        raise ValueError("no full color-5 divider column")

    divider = divider_columns[0]
    left = [row[:divider] for row in grid]
    right = [row[divider + 1:] for row in grid]

    def is_reference(panel):
        return bool(panel and panel[0]) and all(
            value in (0, 4) for row in panel for value in row
        ) and any(value == 4 for row in panel for value in row)

    if is_reference(left) and not is_reference(right):
        reference, template = left, right
    elif is_reference(right) and not is_reference(left):
        reference, template = right, left
    else:
        raise ValueError("could not distinguish reference and template panels")

    reference_rows = [
        {col for col, value in enumerate(row) if value == 4}
        for row in reference
    ]
    marked_rows = [columns for columns in reference_rows if columns]
    if not marked_rows:
        raise ValueError("reference panel has no color-4 rows")
    reference_markers = set.intersection(*marked_rows)
    if not reference_markers:
        raise ValueError("reference rows have no common marker columns")
    reference_marker_columns = sorted(reference_markers)
    special_reference_rows = [
        row_index
        for row_index, columns in enumerate(reference_rows)
        if columns - reference_markers
    ]

    active_template_rows = [
        row for row in template
        if any(value != 5 for value in row)
    ]
    if not active_template_rows:
        raise ValueError("template panel has no active rows")

    nonzero_columns = [
        {col for col, value in enumerate(row) if value not in (0, 5)}
        for row in active_template_rows
    ]
    template_markers = set.intersection(*nonzero_columns)
    if not template_markers:
        raise ValueError("template rows have no common marker columns")
    template_marker_columns = sorted(template_markers)

    if len(reference_marker_columns) != len(template_marker_columns):
        raise ValueError("reference/template marker counts differ")

    base_template_rows = []
    special_template_rows = []
    for row in active_template_rows:
        extras = [
            value for col, value in enumerate(row)
            if col not in template_markers and value not in (0, 5)
        ]
        if not extras:
            base_template_rows.append(row)
            continue
        if len(set(extras)) != 1:
            raise ValueError("template special row has multiple fill colors")
        special_template_rows.append((extras[0], row))

    if not base_template_rows:
        raise ValueError("template has no base row")
    marker_colors = [
        base_template_rows[0][col] for col in template_marker_columns
    ]

    if len(special_reference_rows) != len(special_template_rows):
        raise ValueError("reference/template special-row counts differ")

    output_width = len(reference[0])
    output = [[0] * output_width for _ in range(height)]
    for row in output:
        for col, color in zip(reference_marker_columns, marker_colors):
            row[col] = color

    for row_index, (fill_color, template_row) in zip(
        special_reference_rows, special_template_rows
    ):
        output[row_index] = [fill_color] * output_width
        for reference_col, template_col in zip(
            reference_marker_columns, template_marker_columns
        ):
            output[row_index][reference_col] = template_row[template_col]

    return output


def solve(grid):
    """Decode the 0/4 reference panel and repaint it with the template colors."""
    return _solve_vertical(grid)
