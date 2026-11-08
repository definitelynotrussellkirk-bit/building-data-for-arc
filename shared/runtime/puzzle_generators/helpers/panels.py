"""Helpers for generator inputs made from panel layouts."""
from __future__ import annotations

Grid = list[list[int]]


def assemble_vertical_panels(panels: list[Grid], divider: int = 9) -> Grid:
    """Pad panels to equal height and join them with one divider column."""
    height = max(len(p) for p in panels)
    widths = [len(p[0]) if p else 0 for p in panels]
    out_w = sum(widths) + len(panels) - 1
    out = [[0] * out_w for _ in range(height)]
    col = 0
    for idx, panel in enumerate(panels):
        width = widths[idx]
        for r, row in enumerate(panel):
            for c, value in enumerate(row):
                out[r][col + c] = value
        col += width
        if idx != len(panels) - 1:
            for r in range(height):
                out[r][col] = divider
            col += 1
    return out


def assemble_horizontal_panels(panels: list[Grid], divider: int = 9) -> Grid:
    """Pad panels to equal width and join them with one divider row."""
    width = max(len(p[0]) if p else 0 for p in panels)
    heights = [len(p) for p in panels]
    out_h = sum(heights) + len(panels) - 1
    out = [[0] * width for _ in range(out_h)]
    row = 0
    for idx, panel in enumerate(panels):
        for r, values in enumerate(panel):
            for c, value in enumerate(values):
                out[row + r][c] = value
        row += heights[idx]
        if idx != len(panels) - 1:
            out[row] = [divider] * width
            row += 1
    return out


def paste(grid: Grid, pattern: Grid, top: int, left: int) -> None:
    """Paste a dense pattern into a grid in place."""
    for r, row in enumerate(pattern):
        for c, value in enumerate(row):
            grid[top + r][left + c] = value
