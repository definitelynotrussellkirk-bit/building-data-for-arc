"""Visible-only solution for blind task e3f1bc75d654."""


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or seen[r][c]:
                continue
            stack = [(r, c)]
            seen[r][c] = True
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and grid[nr][nc] == color
                    ):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            r0 = min(rr for rr, _ in cells)
            r1 = max(rr for rr, _ in cells)
            c0 = min(cc for _, cc in cells)
            c1 = max(cc for _, cc in cells)
            out.append(
                {
                    "color": color,
                    "cells": set(cells),
                    "r0": r0,
                    "r1": r1,
                    "c0": c0,
                    "c1": c1,
                    "height": r1 - r0 + 1,
                    "width": c1 - c0 + 1,
                }
            )
    return out


def _border_cells(obj):
    r0, r1, c0, c1 = obj["r0"], obj["r1"], obj["c0"], obj["c1"]
    border = {(r0, c) for c in range(c0, c1 + 1)}
    border.update((r1, c) for c in range(c0, c1 + 1))
    border.update((r, c0) for r in range(r0, r1 + 1))
    border.update((r, c1) for r in range(r0, r1 + 1))
    return border


def solve(grid):
    """Copy the unique bordered pattern into every same-size rectangular frame."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    objects = _components(grid)
    candidates = []
    for obj in objects:
        border = _border_cells(obj)
        if not (border <= obj["cells"]):
            continue
        # Interior pattern pixels need not be 4-connected to the border. Once a
        # complete border identifies an object, include every same-color pixel
        # enclosed by its bounding box.
        enclosed_cells = {
            (r, c)
            for r in range(obj["r0"], obj["r1"] + 1)
            for c in range(obj["c0"], obj["c1"] + 1)
            if grid[r][c] == obj["color"]
        }
        obj["enclosed_cells"] = enclosed_cells
        if enclosed_cells != border:
            candidates.append(obj)

    if not candidates:
        return [row[:] for row in grid]

    # The visible examples contain one source. This tie-break keeps the behavior
    # deterministic if a future input contains more than one bordered pattern.
    source = max(
        candidates,
        key=lambda obj: (len(obj["enclosed_cells"]), obj["height"] * obj["width"]),
    )
    source_mask = {
        (r - source["r0"], c - source["c0"])
        for r, c in source["enclosed_cells"]
    }

    result = [[0 for _ in row] for row in grid]
    target_size = (source["height"], source["width"])
    for obj in objects:
        if (obj["height"], obj["width"]) != target_size:
            continue
        # Matching recipients are complete bordered rectangles; this includes
        # the patterned source itself and excludes arbitrary same-size noise.
        if not (_border_cells(obj) <= obj["cells"]):
            continue
        for dr, dc in source_mask:
            result[obj["r0"] + dr][obj["c0"] + dc] = obj["color"]
    return result
