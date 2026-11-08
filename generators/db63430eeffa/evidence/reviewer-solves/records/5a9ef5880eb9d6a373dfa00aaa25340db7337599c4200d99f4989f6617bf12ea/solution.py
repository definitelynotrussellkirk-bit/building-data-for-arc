"""Visible-example solution for the blind ARC task."""


def _sign(value):
    return (value > 0) - (value < 0)


def _draw_segment(output, start, delta, color=3):
    """Draw an inclusive horizontal, vertical, or 45-degree segment."""
    dr, dc = delta
    length = max(abs(dr), abs(dc))
    if length == 0:
        return
    step_r = _sign(dr)
    step_c = _sign(dc)
    r, c = start
    for _ in range(length + 1):
        if output[r][c] == 0:
            output[r][c] = color
        r += step_r
        c += step_c


def solve(grid):
    """Outline the parallelogram induced by the two azure endpoints.

    The displacement between the two 8-cells is decomposed into its largest
    45-degree component and the remaining horizontal or vertical component.
    Those two vectors span a parallelogram; its four edges are colored green
    while the original azure endpoints remain unchanged.
    """
    output = [row[:] for row in grid]
    endpoints = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    if len(endpoints) != 2:
        return output

    (r0, c0), (r1, c1) = endpoints
    dr, dc = r1 - r0, c1 - c0
    diagonal_length = min(abs(dr), abs(dc))
    diagonal = (_sign(dr) * diagonal_length, _sign(dc) * diagonal_length)
    remainder = (dr - diagonal[0], dc - diagonal[1])

    diagonal_corner = (r0 + diagonal[0], c0 + diagonal[1])
    remainder_corner = (r0 + remainder[0], c0 + remainder[1])

    _draw_segment(output, (r0, c0), diagonal)
    _draw_segment(output, (r0, c0), remainder)
    _draw_segment(output, diagonal_corner, remainder)
    _draw_segment(output, remainder_corner, diagonal)
    return output
