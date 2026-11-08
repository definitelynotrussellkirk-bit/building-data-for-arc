"""Visible-example solve for 2c784862f42b."""
from __future__ import annotations


def _transform(panel, code):
    panel = [row[:] for row in panel]
    if code == 0:
        return panel
    if code == 1:
        return [list(row) for row in zip(*panel[::-1])]
    if code == 2:
        return [row[::-1] for row in panel[::-1]]
    if code == 3:
        return [list(row) for row in zip(*panel)][::-1]
    if code == 4:
        return [row[::-1] for row in panel]
    if code == 5:
        return [row[:] for row in panel[::-1]]
    raise ValueError(f"unexpected transform code {code}")


def solve(grid):
    current = [row[:] for row in grid[:5]]
    codes = grid[5][:4]
    target = grid[5][4]
    panels = []
    for code in codes:
        current = _transform(current, code)
        panels.append([[target if value else 0 for value in row] for row in current])

    output = []
    for row_index in range(5):
        row = []
        for panel_index, panel in enumerate(panels):
            if panel_index:
                row.append(0)
            row.extend(panel[row_index])
        output.append(row)
    return output
