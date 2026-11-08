"""Visible-example-only solution for blind task 4296e507c770."""


def _transform(mask, marker):
    """Apply the transform encoded by marker color 3..6."""
    if marker == 3:  # identity
        return [row[:] for row in mask]
    if marker == 4:  # reflect left/right
        return [list(reversed(row)) for row in mask]
    if marker == 5:  # reflect top/bottom
        return [row[:] for row in reversed(mask)]
    if marker == 6:  # rotate 90 degrees clockwise
        return [list(row) for row in zip(*reversed(mask))]
    raise ValueError(f"unexpected marker color: {marker}")


def solve(grid):
    """Stamp transformed copies of the color-2 template at color 3..6 anchors."""
    height = len(grid)
    width = len(grid[0]) if height else 0

    template_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    if not template_cells:
        return [[0 for _ in range(width)] for _ in range(height)]

    r0 = min(r for r, _ in template_cells)
    r1 = max(r for r, _ in template_cells)
    c0 = min(c for _, c in template_cells)
    c1 = max(c for _, c in template_cells)
    template = [
        [grid[r][c] == 2 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]

    result = [[0 for _ in range(width)] for _ in range(height)]
    for anchor_r, row in enumerate(grid):
        for anchor_c, marker in enumerate(row):
            if marker not in (3, 4, 5, 6):
                continue
            transformed = _transform(template, marker)
            for dr, transformed_row in enumerate(transformed):
                for dc, filled in enumerate(transformed_row):
                    if not filled:
                        continue
                    r = anchor_r + dr
                    c = anchor_c + dc
                    if 0 <= r < height and 0 <= c < width:
                        result[r][c] = 8
    return result
