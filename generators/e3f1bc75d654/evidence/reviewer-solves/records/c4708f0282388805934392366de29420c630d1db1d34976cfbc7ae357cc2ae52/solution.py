"""Visible-example solution for the reviewer-authored e3f1bc75d654 episode."""
from __future__ import annotations


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    frames = []
    colors = sorted({value for row in grid for value in row if value != 0})
    for color in colors:
        cells = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == color
        ]
        rows = [row for row, _col in cells]
        cols = [col for _row, col in cells]
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(cols), max(cols)
        pattern = [
            (row - r0 - 1, col - c0 - 1)
            for row, col in cells
            if r0 < row < r1 and c0 < col < c1
        ]
        frames.append(
            {
                "color": color,
                "bbox": (r0, c0, r1, c1),
                "shape": (r1 - r0 + 1, c1 - c0 + 1),
                "pattern": pattern,
            }
        )

    templates = [frame for frame in frames if frame["pattern"]]
    if len(templates) != 1:
        raise ValueError("expected exactly one frame with a nonempty interior pattern")
    template = templates[0]

    output = [[0 for _ in range(width)] for _ in range(height)]
    for frame in frames:
        if frame["shape"] != template["shape"]:
            continue
        color = frame["color"]
        r0, c0, r1, c1 = frame["bbox"]
        for col in range(c0, c1 + 1):
            output[r0][col] = color
            output[r1][col] = color
        for row in range(r0, r1 + 1):
            output[row][c0] = color
            output[row][c1] = color
        for dr, dc in template["pattern"]:
            output[r0 + 1 + dr][c0 + 1 + dc] = color
    return output
