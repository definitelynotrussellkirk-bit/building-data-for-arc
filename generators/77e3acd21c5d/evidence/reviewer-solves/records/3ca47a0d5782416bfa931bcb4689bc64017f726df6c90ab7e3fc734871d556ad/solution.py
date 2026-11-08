from collections import Counter, deque


def _components(grid, background):
    """Return 8-connected non-background components."""
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == background or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == dc == 0:
                            continue
                        nr, nc = rr + dr, cc + dc
                        if (
                            0 <= nr < h
                            and 0 <= nc < w
                            and grid[nr][nc] != background
                            and (nr, nc) not in seen
                        ):
                            seen.add((nr, nc))
                            queue.append((nr, nc))
            components.append(cells)
    return components


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), max(rows), min(cols), max(cols)


def _axis_targets(position, length, output_length):
    """Project an index to its nearest edge; duplicate exact ties."""
    near_start = position
    near_end = length - 1 - position
    targets = []
    if near_start <= near_end:
        targets.append(near_start)
    if near_end <= near_start:
        targets.append(output_length - 1 - near_end)
    return [target for target in dict.fromkeys(targets) if 0 <= target < output_length]


def solve(grid):
    background = grid[0][0]
    objects = []
    for cells in _components(grid, background):
        r0, r1, c0, c1 = _bbox(cells)
        colors = Counter(grid[r][c] for r, c in cells)
        objects.append(
            {
                "cells": cells,
                "bbox": (r0, r1, c0, c1),
                "height": r1 - r0 + 1,
                "width": c1 - c0 + 1,
                "colors": colors,
            }
        )

    blank_candidates = [obj for obj in objects if len(obj["colors"]) == 1]
    if len(blank_candidates) != 1:
        raise ValueError(f"expected one monochrome blank rectangle, found {len(blank_candidates)}")
    blank = blank_candidates[0]

    marked = [obj for obj in objects if len(obj["colors"]) > 1]
    if not marked:
        raise ValueError("expected at least one marked rectangle")
    source = max(marked, key=lambda obj: obj["width"])

    blank_color = next(iter(blank["colors"]))
    output_h, output_w = blank["height"], blank["width"]
    output = [[blank_color for _ in range(output_w)] for _ in range(output_h)]

    body_color, _ = source["colors"].most_common(1)[0]
    marker_colors = [color for color in source["colors"] if color != body_color]
    if len(marker_colors) != 1:
        raise ValueError(f"expected one marker color, found {marker_colors}")
    marker_color = marker_colors[0]

    r0, _, c0, _ = source["bbox"]
    for r, c in source["cells"]:
        if grid[r][c] != marker_color:
            continue
        local_r, local_c = r - r0, c - c0
        for out_r in _axis_targets(local_r, source["height"], output_h):
            for out_c in _axis_targets(local_c, source["width"], output_w):
                output[out_r][out_c] = marker_color

    return output
