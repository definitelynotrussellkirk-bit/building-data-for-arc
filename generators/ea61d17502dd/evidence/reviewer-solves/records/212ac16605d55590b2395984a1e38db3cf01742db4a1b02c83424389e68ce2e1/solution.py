from collections import Counter


def _strand_colors(values, crossing_index, background):
    """Return (base, marker) for one strand, ignoring its crossing cell."""
    counts = Counter(
        value
        for index, value in enumerate(values)
        if index != crossing_index and value != background
    )
    if len(counts) != 2:
        raise ValueError(f"expected two strand colors, found {dict(counts)}")

    # The two isolated accents are the marker color; the repeated strand color
    # is the base.  The visible lessons keep these counts unequal.
    marker, base = sorted(counts, key=lambda value: (counts[value], value))
    return base, marker


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]

    row_occupancy = [sum(value != background for value in row) for row in grid]
    col_occupancy = [
        sum(grid[row][col] != background for row in range(height))
        for col in range(width)
    ]
    horizontal_row = max(range(height), key=lambda row: row_occupancy[row])
    vertical_col = max(range(width), key=lambda col: col_occupancy[col])

    horizontal_base, horizontal_marker = _strand_colors(
        grid[horizontal_row], vertical_col, background
    )
    vertical_values = [grid[row][vertical_col] for row in range(height)]
    vertical_base, vertical_marker = _strand_colors(
        vertical_values, horizontal_row, background
    )

    horizontal_marker_cols = [
        col for col, value in enumerate(grid[horizontal_row])
        if value == horizontal_marker
    ]
    vertical_marker_rows = [
        row for row in range(height)
        if grid[row][vertical_col] == vertical_marker
    ]
    if len(horizontal_marker_cols) != 2 or len(vertical_marker_rows) != 2:
        raise ValueError("each strand must contain exactly two marker cells")

    left, right = sorted(horizontal_marker_cols)
    top = min(horizontal_row, *vertical_marker_rows)
    bottom = max(horizontal_row, *vertical_marker_rows)

    crossing = grid[horizontal_row][vertical_col]
    if crossing == horizontal_base:
        horizontal_priority = True
    elif crossing == vertical_base:
        horizontal_priority = False
    else:
        raise ValueError("crossing must contain one strand's base color")

    near_vertical_marker = min(
        vertical_marker_rows,
        key=lambda row: (abs(row - horizontal_row), row),
    )
    far_vertical_marker = next(
        row for row in vertical_marker_rows if row != near_vertical_marker
    )
    band_top, band_bottom = sorted((near_vertical_marker, far_vertical_marker))

    output = [[background for _ in range(width)] for _ in range(height)]
    for row in range(top, bottom + 1):
        row_offset = row - top
        inside_vertical_band = band_top <= row <= band_bottom
        for col in range(left, right + 1):
            col_offset = col - left

            if row_offset % 2 == 1:
                if horizontal_priority:
                    value = horizontal_base
                else:
                    value = horizontal_base if col_offset % 2 == 0 else vertical_base
            elif inside_vertical_band:
                if col_offset % 2 == 0:
                    value = vertical_marker
                elif horizontal_priority and row == near_vertical_marker:
                    value = horizontal_base
                else:
                    value = vertical_base
            else:
                value = horizontal_marker if col_offset % 2 == 0 else vertical_base

            output[row][col] = value

    return output
