#!/usr/bin/env python3
"""Adversarial shortcut: infer the bbox from one maximum-area motif pair."""
from __future__ import annotations
import json
import sys
from pathlib import Path


def position(grid, color):
    hits = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    if len(hits) != 1:
        raise ValueError(f"expected one color {color}, got {len(hits)}")
    return hits[0]


def frame(grid, colors):
    origin, px, py = [position(grid, color) for color in colors]
    x = (px[0] - origin[0], px[1] - origin[1])
    y = (py[0] - origin[0], py[1] - origin[1])
    return origin, x, y


def local(frm, r, c):
    origin, x, y = frm
    dr, dc = r - origin[0], c - origin[1]
    return dr * x[0] + dc * x[1], dr * y[0] + dc * y[1]


def global_cell(frm, u, v):
    origin, x, y = frm
    return origin[0] + u * x[0] + v * y[0], origin[1] + u * x[1] + v * y[1]


def solve(grid):
    source = frame(grid, (2, 3, 4))
    target = frame(grid, (5, 6, 7))
    motif = sorted({
        local(source, r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8 and max(map(abs, local(source, r, c))) <= 3
    })
    if len(motif) < 2:
        return [row[:] for row in grid]
    pairs = []
    for i, first in enumerate(motif):
        for second in motif[i + 1:]:
            area_score = abs(first[0] - second[0]) * abs(first[1] - second[1])
            pairs.append((area_score, first, second))
    _, first, second = max(pairs)
    u0, u1 = sorted((first[0], second[0]))
    v0, v1 = sorted((first[1], second[1]))
    out = [row[:] for row in grid]
    for u in range(u0, u1 + 1):
        for v in range(v0, v1 + 1):
            if u in (u0, u1) or v in (v0, v1):
                r, c = global_cell(target, u, v)
                out[r][c] = 8
    return out


if __name__ == "__main__":
    grids = json.loads(Path(sys.argv[1]).read_text())
    one = bool(grids and isinstance(grids[0][0], int))
    if one:
        grids = [grids]
    outputs = [solve(grid) for grid in grids]
    Path(sys.argv[2]).write_text(json.dumps(outputs[0] if one else outputs, separators=(",", ":")) + "\n")
