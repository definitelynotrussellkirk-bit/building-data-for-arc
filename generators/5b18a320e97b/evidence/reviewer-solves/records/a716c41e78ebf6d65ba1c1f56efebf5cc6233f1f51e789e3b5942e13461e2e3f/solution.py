from collections import defaultdict


def solve(grid):
    """Compress the colored guide lines around the solid 5-square.

    Every nonzero, non-5 color forms one horizontal or vertical guide line.
    The 5-square gives the output side length.  Preserve the guide-line order
    and expand each color into a full output stripe.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0

    five_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    ]
    if not five_cells:
        raise ValueError("expected a solid square of color 5")

    five_rows = [r for r, _ in five_cells]
    five_cols = [c for _, c in five_cells]
    side_h = max(five_rows) - min(five_rows) + 1
    side_w = max(five_cols) - min(five_cols) + 1
    if side_h != side_w or len(five_cells) != side_h * side_w:
        raise ValueError("color 5 must form one solid square")
    side = side_h

    cells_by_color = defaultdict(list)
    for r, row in enumerate(grid):
        if len(row) != width:
            raise ValueError("grid must be rectangular")
        for c, value in enumerate(row):
            if value not in (0, 5):
                cells_by_color[value].append((r, c))

    if len(cells_by_color) != side:
        raise ValueError("expected one guide-line color per output stripe")

    horizontal_score = 0
    vertical_score = 0
    for cells in cells_by_color.values():
        row_span = max(r for r, _ in cells) - min(r for r, _ in cells)
        col_span = max(c for _, c in cells) - min(c for _, c in cells)
        if col_span > row_span:
            horizontal_score += 1
        elif row_span > col_span:
            vertical_score += 1

    if horizontal_score > vertical_score:
        ordered = sorted(
            cells_by_color,
            key=lambda color: min(r for r, _ in cells_by_color[color]),
        )
        return [[color] * side for color in ordered]

    if vertical_score > horizontal_score:
        ordered = sorted(
            cells_by_color,
            key=lambda color: min(c for _, c in cells_by_color[color]),
        )
        return [ordered[:] for _ in range(side)]

    raise ValueError("could not determine guide-line orientation")
