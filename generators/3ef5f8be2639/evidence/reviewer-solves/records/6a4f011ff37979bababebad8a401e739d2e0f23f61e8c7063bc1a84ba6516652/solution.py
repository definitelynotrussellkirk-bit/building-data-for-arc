"""Visible-example-only solution for blind task 3ef5f8be2639."""

from __future__ import annotations

from fractions import Fraction
from math import ceil, floor
from typing import Sequence


def _choose_red_green_pair(grid: Sequence[Sequence[int]]) -> tuple[tuple[int, int], tuple[int, int]]:
    red: list[tuple[int, int]] = []
    green: list[tuple[int, int]] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 2:
                red.append((r, c))
            elif value == 3:
                green.append((r, c))

    if not red or not green:
        raise ValueError("expected at least one red (2) and one green (3) cell")

    # Maximize squared distance.  On the only visible tie, preferring the pair
    # with the larger vertical component selects the demonstrated orientation.
    candidates: list[tuple[tuple[int, int, int, int, int], tuple[int, int], tuple[int, int]]] = []
    for rp in red:
        for gp in green:
            dr = rp[0] - gp[0]
            dc = rp[1] - gp[1]
            key = (
                dr * dr + dc * dc,
                abs(dr),
                abs(dc),
                -min(rp[0], gp[0]),
                -min(rp[1], gp[1]),
            )
            candidates.append((key, rp, gp))
    _, rp, gp = max(candidates, key=lambda item: item[0])
    return rp, gp


def solve(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Rotate the farthest red-green segment by 90 degrees and fill its box."""
    if not grid or not grid[0]:
        return []
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    (r1, c1), (r2, c2) = _choose_red_green_pair(grid)

    # Rotated endpoints around the original midpoint.  Fractions preserve the
    # half-cell geometry seen in the visible adjacent-pixel example.
    endpoint_a = (
        Fraction(r1 + r2 - (c2 - c1), 2),
        Fraction(c1 + c2 + (r2 - r1), 2),
    )
    endpoint_b = (
        Fraction(r1 + r2 + (c2 - c1), 2),
        Fraction(c1 + c2 - (r2 - r1), 2),
    )

    top = floor(min(endpoint_a[0], endpoint_b[0]))
    bottom = ceil(max(endpoint_a[0], endpoint_b[0]))
    left = floor(min(endpoint_a[1], endpoint_b[1]))
    right = ceil(max(endpoint_a[1], endpoint_b[1]))

    height = len(grid)
    out = [[0 for _ in range(width)] for _ in range(height)]
    for r in range(max(0, top), min(height - 1, bottom) + 1):
        for c in range(max(0, left), min(width - 1, right) + 1):
            out[r][c] = 8
    return out
