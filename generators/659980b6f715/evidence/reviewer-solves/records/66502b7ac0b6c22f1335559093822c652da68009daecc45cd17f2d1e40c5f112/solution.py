"""Visible-example solver for normalized colored-shape overlay."""


def solve(grid):
    colors = sorted({value for row in grid for value in row if value != 0})
    if len(colors) != 2:
        raise ValueError(f"expected two non-background colors, found {colors}")

    normalized = {}
    for color in colors:
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                 if value == color]
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        normalized[color] = {(r - r0, c - c0) for r, c in cells}

    low, high = colors
    a, b = normalized[low], normalized[high]
    union = a | b
    height = 1 + max(r for r, _ in union)
    width = 1 + max(c for _, c in union)
    return [
        [
            9 if (r, c) in a and (r, c) in b
            else low if (r, c) in a
            else high if (r, c) in b
            else 0
            for c in range(width)
        ]
        for r in range(height)
    ]
