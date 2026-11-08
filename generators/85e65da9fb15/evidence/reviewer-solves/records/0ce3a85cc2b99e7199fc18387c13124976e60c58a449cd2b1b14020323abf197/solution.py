"""Visible-example solution for ARC task 85e65da9fb15."""
from __future__ import annotations


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
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
            r1 = min(rr for rr, _ in cells)
            r2 = max(rr for rr, _ in cells)
            c1 = min(cc for _, cc in cells)
            c2 = max(cc for _, cc in cells)
            out.append(
                {
                    "color": color,
                    "cells": cells,
                    "r1": r1,
                    "r2": r2,
                    "c1": c1,
                    "c2": c2,
                    "h": r2 - r1 + 1,
                    "w": c2 - c1 + 1,
                }
            )
    return out


def _is_frame(obj):
    if obj["h"] < 3 or obj["w"] < 3:
        return False
    expected = {
        (r, c)
        for r in range(obj["r1"], obj["r2"] + 1)
        for c in range(obj["c1"], obj["c2"] + 1)
        if r in (obj["r1"], obj["r2"]) or c in (obj["c1"], obj["c2"])
    }
    return set(obj["cells"]) == expected


def _shape_grid(obj):
    shape = [[0] * obj["w"] for _ in range(obj["h"])]
    for r, c in obj["cells"]:
        shape[r - obj["r1"]][c - obj["c1"]] = obj["color"]
    return shape


def _rotate_cw(shape):
    return [list(row) for row in zip(*shape[::-1])]


def solve(grid):
    objects = _components(grid)
    frames = sorted(
        (obj for obj in objects if _is_frame(obj)),
        key=lambda obj: (obj["r1"], obj["c1"]),
    )
    loose = sorted(
        (obj for obj in objects if not _is_frame(obj)),
        key=lambda obj: (obj["r1"], obj["c1"]),
    )

    result = [[0] * len(grid[0]) for _ in grid]
    for frame in frames:
        for r, c in frame["cells"]:
            result[r][c] = frame["color"]

    used_frames = set()
    for obj in loose:
        original = _shape_grid(obj)
        rotated = _rotate_cw(original)
        candidates = []
        for index, frame in enumerate(frames):
            if index in used_frames:
                continue
            interior_h = frame["h"] - 2
            interior_w = frame["w"] - 2
            oriented = None
            # The examples preserve orientation whenever it already fits.
            if len(original) <= interior_h and len(original[0]) <= interior_w:
                oriented = original
            elif len(rotated) <= interior_h and len(rotated[0]) <= interior_w:
                oriented = rotated
            if oriented is None:
                continue
            unused_bbox_area = (
                interior_h * interior_w - len(oriented) * len(oriented[0])
            )
            candidates.append(
                (
                    unused_bbox_area,
                    frame["r1"],
                    frame["c1"],
                    index,
                    frame,
                    oriented,
                )
            )
        if not candidates:
            continue
        _, _, _, frame_index, frame, oriented = min(
            candidates, key=lambda row: row[:3]
        )
        used_frames.add(frame_index)
        interior_h = frame["h"] - 2
        interior_w = frame["w"] - 2
        start_r = frame["r1"] + 1 + (interior_h - len(oriented)) // 2
        start_c = frame["c1"] + 1 + (interior_w - len(oriented[0])) // 2
        for dr, row in enumerate(oriented):
            for dc, value in enumerate(row):
                if value:
                    result[start_r + dr][start_c + dc] = value
    return result
