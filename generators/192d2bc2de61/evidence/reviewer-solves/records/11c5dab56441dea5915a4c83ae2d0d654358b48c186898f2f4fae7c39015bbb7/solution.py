"""Visible-example solution for task 192d2bc2de61."""


def solve(grid):
    """Reorder and pack the lower colored glyphs using the upper color key.

    The input has two regions separated by the largest vertical run of blank
    rows.  The first non-blank row of the upper region gives the desired
    left-to-right color order.  Each color's glyph is cropped from the lower
    region, then the glyphs are placed side by side with one blank column,
    top-aligned in a background-zero canvas.
    """
    if not grid or not grid[0]:
        return []

    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    nonblank_rows = [r for r, row in enumerate(grid) if any(value != 0 for value in row)]
    if len(nonblank_rows) < 2:
        return [row[:] for row in grid]

    # The largest gap between occupied rows separates the sparse key above
    # from the glyph bank below.
    _, lower_start = max(
        ((b - a, b) for a, b in zip(nonblank_rows, nonblank_rows[1:])),
        key=lambda item: item[0],
    )

    upper_nonblank = [r for r in nonblank_rows if r < lower_start]
    if not upper_nonblank:
        raise ValueError("missing upper color-order key")

    order = []
    seen = set()
    for value in grid[upper_nonblank[0]]:
        if value != 0 and value not in seen:
            order.append(value)
            seen.add(value)

    if not order:
        raise ValueError("upper key contains no colors")

    glyphs = []
    for color in order:
        cells = [
            (r, c)
            for r in range(lower_start, len(grid))
            for c in range(width)
            if grid[r][c] == color
        ]
        if not cells:
            raise ValueError(f"missing lower glyph for color {color}")

        min_r = min(r for r, _ in cells)
        max_r = max(r for r, _ in cells)
        min_c = min(c for _, c in cells)
        max_c = max(c for _, c in cells)
        glyphs.append(
            [row[min_c : max_c + 1] for row in grid[min_r : max_r + 1]]
        )

    out_height = max(len(glyph) for glyph in glyphs)
    out_width = sum(len(glyph[0]) for glyph in glyphs) + len(glyphs) - 1
    output = [[0] * out_width for _ in range(out_height)]

    col_offset = 0
    for glyph in glyphs:
        for r, row in enumerate(glyph):
            output[r][col_offset : col_offset + len(row)] = row
        col_offset += len(glyph[0]) + 1

    return output
