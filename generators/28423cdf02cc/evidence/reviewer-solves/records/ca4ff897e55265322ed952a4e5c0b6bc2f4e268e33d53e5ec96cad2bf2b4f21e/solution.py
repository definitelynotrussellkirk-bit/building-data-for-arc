from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Stamp the top-left 3x3 template, centered on every blue marker."""
    output = [row[:] for row in grid]
    template = [row[:3] for row in grid[:3]]
    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]
    height = len(grid)
    width = len(grid[0])
    for center_r, center_c in markers:
        for template_r in range(3):
            for template_c in range(3):
                r = center_r - 1 + template_r
                c = center_c - 1 + template_c
                if 0 <= r < height and 0 <= c < width:
                    output[r][c] = template[template_r][template_c]
    return output
