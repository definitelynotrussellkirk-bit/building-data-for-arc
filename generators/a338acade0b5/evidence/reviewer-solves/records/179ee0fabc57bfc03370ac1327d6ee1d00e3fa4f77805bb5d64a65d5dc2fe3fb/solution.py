"""Visible-only solution for blind task a338acade0b5."""


def solve(grid):
    points = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if len(points) != 2:
        raise ValueError(f"expected exactly two non-background cells, got {len(points)}")

    (r1, c1, color1), (r2, c2, color2) = points
    if color1 != color2:
        raise ValueError("expected both endpoints to have the same color")

    # The examples encode the inclusive length of the straight horizontal,
    # vertical, or 45-degree segment joining the two markers.
    length = max(abs(r2 - r1), abs(c2 - c1)) + 1
    output_color = {2: 8, 8: 2}.get(color1, color1)
    return [[output_color] * length]
