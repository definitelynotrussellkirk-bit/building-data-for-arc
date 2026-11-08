from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Decode the stencil library above the blank separator and stamp the body seeds."""
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    try:
        separator_row = next(
            r for r, row in enumerate(grid) if all(value == 0 for value in row)
        )
    except StopIteration as exc:
        raise ValueError("grid has no all-zero separator row") from exc
    if separator_row == 0 or separator_row == height - 1:
        raise ValueError("separator must lie between the library and body")

    divider_columns = [
        c
        for c in range(width)
        if all(grid[r][c] == 9 for r in range(separator_row))
    ]
    if not divider_columns:
        raise ValueError("library has no full-height 9 divider columns")

    boundaries = [-1, *divider_columns, width]
    stencils: dict[int, list[tuple[int, int]]] = {}

    for left_boundary, right_boundary in zip(boundaries, boundaries[1:]):
        left = left_boundary + 1
        right = right_boundary
        if left >= right:
            continue

        anchors: list[tuple[int, int]] = []
        colored_cells: list[tuple[int, int, int]] = []
        for r in range(separator_row):
            for c in range(left, right):
                value = grid[r][c]
                if value == 9:
                    anchors.append((r, c))
                elif value != 0:
                    colored_cells.append((r, c, value))

        if not anchors and not colored_cells:
            continue
        if len(anchors) != 1:
            raise ValueError("each library panel must contain exactly one 9 anchor")
        if not colored_cells:
            raise ValueError("each library panel must contain a colored stencil")

        colors = {value for _, _, value in colored_cells}
        if len(colors) != 1:
            raise ValueError("each library panel must use exactly one stencil color")
        color = next(iter(colors))
        if color in stencils:
            raise ValueError("stencil colors must be unique across panels")

        anchor_r, anchor_c = anchors[0]
        stencils[color] = [
            (r - anchor_r, c - anchor_c) for r, c, _ in colored_cells
        ]

    output = [[0 for _ in range(width)] for _ in range(height)]
    for r in range(separator_row + 1, height):
        for c in range(width):
            color = grid[r][c]
            offsets = stencils.get(color)
            if offsets is None:
                continue
            for dr, dc in offsets:
                rr, cc = r + dr, c + dc
                if 0 <= rr < height and 0 <= cc < width:
                    output[rr][cc] = color

    return output
