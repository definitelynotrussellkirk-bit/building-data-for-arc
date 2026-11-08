from collections import Counter
from copy import deepcopy


def _background(grid):
    flat = [value for row in grid for value in row]
    counts = Counter(flat)
    first = {value: flat.index(value) for value in counts}
    return max(counts, key=lambda value: (counts[value], -first[value]))


def _components(grid, background):
    h, w = len(grid), len(grid[0])
    seen = set()
    parts = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == background:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
            parts.append(
                {
                    "index": len(parts),
                    "color": color,
                    "cells": cells,
                    "size": len(cells),
                    "r1": r1,
                    "r2": r2,
                    "c1": c1,
                    "c2": c2,
                    "h": r2 - r1 + 1,
                    "w": c2 - c1 + 1,
                    "solid": len(cells) == (r2 - r1 + 1) * (c2 - c1 + 1),
                }
            )
    return parts


def _overlaps(a1, a2, b1, b2):
    return a1 <= b2 and b1 <= a2


def _candidates(parts):
    found = []
    for mover in parts:
        for wall in parts:
            if mover is wall or not wall["solid"]:
                continue
            direction = None
            gap = None
            if (
                wall["r1"] > mover["r2"]
                and _overlaps(mover["c1"], mover["c2"], wall["c1"], wall["c2"])
                and wall["w"] > mover["w"]
            ):
                direction = "down"
                gap = wall["r1"] - mover["r2"] - 1
            elif (
                mover["r1"] > wall["r2"]
                and _overlaps(mover["c1"], mover["c2"], wall["c1"], wall["c2"])
                and wall["w"] > mover["w"]
            ):
                direction = "up"
                gap = mover["r1"] - wall["r2"] - 1
            elif (
                wall["c1"] > mover["c2"]
                and _overlaps(mover["r1"], mover["r2"], wall["r1"], wall["r2"])
                and wall["h"] > mover["h"]
            ):
                direction = "right"
                gap = wall["c1"] - mover["c2"] - 1
            elif (
                mover["c1"] > wall["c2"]
                and _overlaps(mover["r1"], mover["r2"], wall["r1"], wall["r2"])
                and wall["h"] > mover["h"]
            ):
                direction = "left"
                gap = mover["c1"] - wall["c2"] - 1
            if direction is not None:
                found.append(
                    {
                        "order": len(found),
                        "mover": mover,
                        "wall": wall,
                        "direction": direction,
                        "gap": gap,
                    }
                )
    return sorted(found, key=lambda x: (x["gap"], -x["wall"]["size"], x["order"]))


def _put(grid, r, c, value):
    if 0 <= r < len(grid) and 0 <= c < len(grid[0]):
        grid[r][c] = value


def solve(grid):
    background = _background(grid)
    parts = _components(grid, background)
    candidates = _candidates(parts)
    if not candidates:
        return deepcopy(grid)

    chosen = candidates[0]
    mover = chosen["mover"]
    wall = chosen["wall"]
    direction = chosen["direction"]
    out = deepcopy(grid)
    payload = [(r, c, grid[r][c]) for r, c in mover["cells"]]

    for r, c, _ in payload:
        out[r][c] = background

    if direction in ("down", "up"):
        for r in range(wall["r1"], wall["r2"] + 1):
            for c in range(mover["c1"], mover["c2"] + 1):
                _put(out, r, c, background)
        pad = max(1, mover["w"] // 2)
        for r in range(wall["r1"], wall["r2"] + 1):
            for d in range(1, pad + 1):
                _put(out, r, wall["c1"] - d, wall["color"])
                _put(out, r, wall["c2"] + d, wall["color"])
        if direction == "up":
            dest_r = max(0, wall["r1"] - mover["h"])
        elif wall["r2"] == len(grid) - 1:
            dest_r = wall["r2"] - mover["h"] + 1
        else:
            dest_r = wall["r2"] + 1
        dest_c = mover["c1"]
    else:
        for r in range(mover["r1"], mover["r2"] + 1):
            for c in range(wall["c1"], wall["c2"] + 1):
                _put(out, r, c, background)
        pad = max(1, mover["h"] // 2)
        for c in range(wall["c1"], wall["c2"] + 1):
            for d in range(1, pad + 1):
                _put(out, wall["r1"] - d, c, wall["color"])
                _put(out, wall["r2"] + d, c, wall["color"])
        if direction == "left":
            dest_c = max(0, wall["c1"] - mover["w"])
        elif wall["c2"] == len(grid[0]) - 1:
            dest_c = wall["c2"] - mover["w"] + 1
        else:
            dest_c = wall["c2"] + 1
        dest_r = mover["r1"]

    for r, c, value in payload:
        _put(out, dest_r + r - mover["r1"], dest_c + c - mover["c1"], value)
    return out
