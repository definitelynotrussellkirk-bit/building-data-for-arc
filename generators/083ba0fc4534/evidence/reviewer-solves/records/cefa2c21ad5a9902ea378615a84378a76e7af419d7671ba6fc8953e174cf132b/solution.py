"""Visible-only solution for task 083ba0fc4534.

The input contains three equal-sized panels separated by full-height columns of
color 5.  The output is the cellwise majority vote across the three panels.
"""

from collections import Counter


def _split_panels(grid):
    if not grid or not grid[0]:
        return []
    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    separators = [
        c for c in range(width)
        if all(grid[r][c] == 5 for r in range(height))
    ]
    if not separators:
        raise ValueError("no full-height color-5 separators found")

    panels = []
    start = 0
    for stop in separators + [width]:
        if stop > start:
            panels.append([row[start:stop] for row in grid])
        start = stop + 1

    if len(panels) != 3:
        raise ValueError(f"expected three panels, found {len(panels)}")
    panel_widths = {len(panel[0]) for panel in panels}
    if len(panel_widths) != 1:
        raise ValueError("panels must have equal widths")
    return panels


def solve(grid):
    panels = _split_panels(grid)
    if not panels:
        return []

    height = len(grid)
    width = len(panels[0][0])
    output = [[0] * width for _ in range(height)]

    for r in range(height):
        for c in range(width):
            values = [panel[r][c] for panel in panels]
            value, count = Counter(values).most_common(1)[0]
            # Three voters guarantee a unique majority only when count >= 2.
            output[r][c] = value if count >= 2 else 0
    return output
