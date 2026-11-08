from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill the hollow gray frame with a two-color quadrant checkerboard."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0])

    gray = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5]
    if not gray:
        return out

    top = min(r for r, _ in gray)
    bottom = max(r for r, _ in gray)
    left = min(c for _, c in gray)
    right = max(c for _, c in gray)

    clues = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]
    if len(clues) != 2 or bottom - top < 2 or right - left < 2:
        return out

    # The clue nearest the canvas's top-right corner supplies the main
    # (top-left/bottom-right) diagonal; the other supplies the anti-diagonal.
    corner_r, corner_c = 0, width - 1
    clues.sort(key=lambda item: ((item[0] - corner_r) ** 2 + (item[1] - corner_c) ** 2, item[0], -item[1]))
    main_color = clues[0][2]
    anti_color = clues[1][2]

    interior_height = bottom - top - 1
    interior_width = right - left - 1
    top_rows = (interior_height + 1) // 2
    left_cols = (interior_width + 1) // 2

    for r in range(top + 1, bottom):
        in_top = r - (top + 1) < top_rows
        for c in range(left + 1, right):
            in_left = c - (left + 1) < left_cols
            out[r][c] = main_color if in_top == in_left else anti_color

    return out
