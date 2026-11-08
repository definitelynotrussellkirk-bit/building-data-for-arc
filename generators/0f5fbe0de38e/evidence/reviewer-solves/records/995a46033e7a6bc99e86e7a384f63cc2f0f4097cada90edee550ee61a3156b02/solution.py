"""Visible-example solver for the post-repair episode."""
from collections import Counter


DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIR8 = DIR4 + ((-1, -1), (-1, 1), (1, -1), (1, 1))


def _components(grid, background, *, same_color, directions):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == background or (r, c) in seen:
                continue
            start_color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in directions:
                    nr, nc = cr + dr, cc + dc
                    if not (0 <= nr < h and 0 <= nc < w) or (nr, nc) in seen:
                        continue
                    if grid[nr][nc] == background:
                        continue
                    if same_color and grid[nr][nc] != start_color:
                        continue
                    seen.add((nr, nc))
                    stack.append((nr, nc))
            rows = [p[0] for p in cells]
            cols = [p[1] for p in cells]
            r1, c1, r2, c2 = min(rows), min(cols), max(rows), max(cols)
            result.append({
                "cells": tuple(cells),
                "cell_set": frozenset(cells),
                "r1": r1,
                "c1": c1,
                "r2": r2,
                "c2": c2,
                "h": r2 - r1 + 1,
                "w": c2 - c1 + 1,
                "size": len(cells),
                "colors": tuple(sorted({grid[x][y] for x, y in cells})),
                "color": start_color if same_color else None,
            })
    return result


def _gap_distance(a, b):
    row_gap = max(0, max(a["r1"], b["r1"]) - min(a["r2"], b["r2"]) - 1)
    col_gap = max(0, max(a["c1"], b["c1"]) - min(a["c2"], b["c2"]) - 1)
    return row_gap + col_gap


def _xform(cell, transform, th, tw):
    r, c = cell[0], cell[1]
    if transform == 0:
        return r, c
    if transform == 1:
        return c, th - 1 - r
    if transform == 2:
        return th - 1 - r, tw - 1 - c
    if transform == 3:
        return tw - 1 - c, r
    if transform == 4:
        return r, tw - 1 - c
    if transform == 5:
        return th - 1 - r, c
    if transform == 6:
        return c, r
    return tw - 1 - c, th - 1 - r


def solve(grid):
    h, w = len(grid), len(grid[0])
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]

    multi = _components(grid, background, same_color=False, directions=DIR8)
    candidates = [obj for obj in multi if len(obj["colors"]) >= 3]
    if not candidates:
        return [row[:] for row in grid]
    template = min(candidates, key=lambda obj: (obj["size"], obj["r1"], obj["c1"]))
    template_colors = [grid[r][c] for r, c in template["cells"]]
    fill_color = Counter(template_colors).most_common(1)[0][0]
    marker_colors = {color for color in template["colors"] if color != fill_color}
    th, tw = template["h"], template["w"]

    template_cells = [
        (r - template["r1"], c - template["c1"], grid[r][c])
        for r, c in template["cells"]
    ]
    marker_cells = [cell for cell in template_cells if cell[2] != fill_color]
    fill_cells = [cell for cell in template_cells if cell[2] == fill_color]

    monochrome = _components(grid, background, same_color=True, directions=DIR4)
    marker_objects = [
        obj for obj in monochrome
        if obj["color"] in marker_colors and not (obj["cell_set"] & template["cell_set"])
    ]
    marker_objects.sort(key=lambda obj: (obj["r1"], obj["c1"]))

    candidates = []
    for i in range(len(marker_objects)):
        for j in range(i + 1, len(marker_objects)):
            if marker_objects[i]["color"] != marker_objects[j]["color"]:
                candidates.append((_gap_distance(marker_objects[i], marker_objects[j]), i, j))
    candidates.sort(key=lambda row: row[0])
    pairs = []
    used = set()
    for _distance, i, j in candidates:
        if i in used or j in used:
            continue
        pairs.append((marker_objects[i], marker_objects[j]))
        used.update((i, j))

    out = [row[:] for row in grid]
    for a, b in pairs:
        if a["h"] != b["h"] or a["w"] != b["w"]:
            continue
        sh, sw = a["h"], a["w"]
        placement = None
        for transform in range(8):
            transformed_markers = [_xform(cell, transform, th, tw) for cell in marker_cells]
            for first, second in ((a, b), (b, a)):
                anchor1 = (
                    first["r1"] - transformed_markers[0][0] * sh,
                    first["c1"] - transformed_markers[0][1] * sw,
                )
                anchor2 = (
                    second["r1"] - transformed_markers[1][0] * sh,
                    second["c1"] - transformed_markers[1][1] * sw,
                )
                if anchor1 == anchor2:
                    placement = (anchor1, [_xform(cell, transform, th, tw) for cell in fill_cells])
                    break
            if placement is not None:
                break
        if placement is None:
            continue
        (start_r, start_c), transformed_fill = placement
        for cell_r, cell_c in transformed_fill:
            for r in range(start_r + cell_r * sh, start_r + (cell_r + 1) * sh):
                for c in range(start_c + cell_c * sw, start_c + (cell_c + 1) * sw):
                    if 0 <= r < h and 0 <= c < w and out[r][c] == background:
                        out[r][c] = fill_color
    return out
