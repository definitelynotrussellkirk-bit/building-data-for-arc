from collections import Counter


def solve(grid):
    h = len(grid)
    w = len(grid[0])

    # The only all-gray column separates the two panels.
    divider = next(
        c for c in range(w)
        if all(grid[r][c] == 5 for r in range(h))
    )

    def panel(c0, c1):
        return [
            list(row[c0:c1])
            for row in grid
            if any(value != 5 for value in row[c0:c1])
        ]

    left = panel(0, divider)
    right = panel(divider + 1, w)

    def is_reference(rows):
        return all(value in (0, 4) for row in rows for value in row)

    if is_reference(left):
        reference, template = left, right
    else:
        reference, template = right, left

    # The template mode is the ordinary vertical-line row.  Other template
    # rows are special fill/retention variants, in top-to-bottom order.
    counts = Counter(tuple(row) for row in template)
    template_normal = list(max(counts, key=counts.get))
    template_line_cols = [
        c for c, value in enumerate(template_normal) if value != 0
    ]
    line_colors = [template_normal[c] for c in template_line_cols]
    template_specials = [
        row for row in template if row != template_normal
    ]

    # The sparsest positive-yellow reference pattern marks output line
    # positions.  Every other positive-yellow pattern marks a special row.
    yellow_count = lambda row: sum(value == 4 for value in row)
    positive_rows = [row for row in reference if yellow_count(row) > 0]
    minimum = min(yellow_count(row) for row in positive_rows)
    reference_normal = next(
        row for row in positive_rows if yellow_count(row) == minimum
    )
    reference_line_cols = [
        c for c, value in enumerate(reference_normal) if value == 4
    ]
    reference_special_indices = [
        r for r, row in enumerate(reference)
        if yellow_count(row) > 0 and row != reference_normal
    ]
    special_number = {
        row_index: order
        for order, row_index in enumerate(reference_special_indices)
    }

    off_line_cols = [
        c for c in range(len(template_normal))
        if c not in template_line_cols
    ]

    output = [[0] * len(reference[0]) for _ in reference]
    for r in range(len(reference)):
        if r not in special_number:
            for out_col, color in zip(reference_line_cols, line_colors):
                output[r][out_col] = color
            continue

        special = template_specials[special_number[r]]
        fill = special[off_line_cols[0]]
        output[r] = [fill] * len(reference[0])
        for template_col, out_col, line_color in zip(
            template_line_cols, reference_line_cols, line_colors
        ):
            if special[template_col] == line_color:
                output[r][out_col] = line_color

    return output
