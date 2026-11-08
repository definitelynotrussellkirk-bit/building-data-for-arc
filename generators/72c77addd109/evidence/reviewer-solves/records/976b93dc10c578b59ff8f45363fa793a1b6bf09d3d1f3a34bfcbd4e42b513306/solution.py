"""Visible-example solution for the reviewer solve episode."""
from __future__ import annotations


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    found = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            found.append({"color": color, "cells": cells})
    return found


def _bbox(obj):
    rows = [r for r, _ in obj["cells"]]
    cols = [c for _, c in obj["cells"]]
    return min(rows), min(cols), max(rows), max(cols)


def _is_frame(obj):
    r1, c1, r2, c2 = _bbox(obj)
    if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
        return False
    border = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    return set(obj["cells"]) == border


def solve(grid):
    """Rank solid components and hollow frames by area, then center-paste."""
    pieces = _components(grid)
    frames = [piece for piece in pieces if _is_frame(piece)]
    solids = [piece for piece in pieces if not _is_frame(piece)]

    def frame_area(frame):
        r1, c1, r2, c2 = _bbox(frame)
        return (r2 - r1 - 1) * (c2 - c1 - 1)

    frames.sort(key=frame_area)
    solids.sort(key=lambda piece: len(piece["cells"]))

    out = [[0 for _ in row] for row in grid]
    for frame in frames:
        for r, c in frame["cells"]:
            out[r][c] = frame["color"]

    for solid, frame in zip(solids, frames):
        sr1, sc1, sr2, sc2 = _bbox(solid)
        fr1, fc1, fr2, fc2 = _bbox(frame)
        crop_h = sr2 - sr1 + 1
        crop_w = sc2 - sc1 + 1
        interior_h = fr2 - fr1 - 1
        interior_w = fc2 - fc1 - 1
        top = fr1 + 1 + (interior_h - crop_h) // 2
        left = fc1 + 1 + (interior_w - crop_w) // 2
        for r, c in solid["cells"]:
            out[top + r - sr1][left + c - sc1] = solid["color"]
    return out
