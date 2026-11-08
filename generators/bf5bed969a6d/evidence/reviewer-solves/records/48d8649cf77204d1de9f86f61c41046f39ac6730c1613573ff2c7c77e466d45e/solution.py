"""Visible-only solution for the assigned blind ARC instance."""


def solve(grid):
    """Stamp the red template, recolored, into each hollow frame's center."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    red = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == 2]
    if not red:
        return out

    red_r0 = min(r for r, _ in red)
    red_r1 = max(r for r, _ in red)
    red_c0 = min(c for _, c in red)
    red_c1 = max(c for _, c in red)
    template = {
        (r - red_r0, c - red_c0)
        for r, c in red
    }
    template_h = red_r1 - red_r0 + 1
    template_w = red_c1 - red_c0 + 1

    # The red object is a movable template, not part of the output.
    for r, c in red:
        out[r][c] = 0

    frame_colors = sorted({cell for row in grid for cell in row if cell not in (0, 2)})
    for color in frame_colors:
        cells = [
            (r, c)
            for r in range(height)
            for c in range(width)
            if grid[r][c] == color
        ]
        if not cells:
            continue

        r0 = min(r for r, _ in cells)
        r1 = max(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        c1 = max(c for _, c in cells)
        inner_h = r1 - r0 - 1
        inner_w = c1 - c0 - 1
        if template_h > inner_h or template_w > inner_w:
            continue

        top = r0 + 1 + (inner_h - template_h) // 2
        left = c0 + 1 + (inner_w - template_w) // 2
        for dr, dc in template:
            out[top + dr][left + dc] = color

    return out
