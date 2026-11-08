def solve(grid):
    """Fill the hollow gray frame with a two-color diagonal block checker."""
    out = [row[:] for row in grid]

    gray = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5]
    if not gray:
        return out

    top = min(r for r, _ in gray)
    bottom = max(r for r, _ in gray)
    left = min(c for _, c in gray)
    right = max(c for _, c in gray)

    markers = sorted(
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    )
    if len(markers) != 2 or bottom - top < 2 or right - left < 2:
        return out

    frame_width = right - left + 1
    first_color = markers[0][2]
    second_color = markers[1][2]
    diagonal_color, off_diagonal_color = (
        (first_color, second_color)
        if frame_width % 2 == 0
        else (second_color, first_color)
    )

    interior_height = bottom - top - 1
    interior_width = right - left - 1
    upper_rows = (interior_height + 1) // 2
    left_columns = (interior_width + 1) // 2

    for r_offset in range(interior_height):
        for c_offset in range(interior_width):
            upper = r_offset < upper_rows
            left_half = c_offset < left_columns
            out[top + 1 + r_offset][left + 1 + c_offset] = (
                diagonal_color if upper == left_half else off_diagonal_color
            )

    return out
