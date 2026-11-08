"""Visible-example solution for the crossing-band scalar task."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Return the clean row color, or the anomaly in the near-uniform row."""
    if not grid or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")

    for row in grid:
        color = row[0]
        if color != 0 and all(value == color for value in row):
            return [[color]]

    for row in grid:
        major = row[0]
        if major == 0:
            continue
        anomalies = [value for value in row if value != major]
        if len(anomalies) == 1:
            return [[anomalies[0]]]

    raise ValueError("no clean row or single-anomaly dirty row found")
