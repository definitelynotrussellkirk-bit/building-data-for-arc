"""Visible-example solution for 089c14df9952."""
from __future__ import annotations


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp = []
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == dc == 0:
                            continue
                        nr, nc = rr + dr, cc + dc
                        if (
                            0 <= nr < h
                            and 0 <= nc < w
                            and grid[nr][nc] != 0
                            and (nr, nc) not in seen
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            result.append(comp)
    return result


def _spin(point, index):
    r, c = point
    transforms = (
        (r, c),
        (c, -r),
        (-r, -c),
        (-c, r),
        (r, -c),
        (-c, -r),
        (-r, c),
        (c, r),
    )
    return transforms[index]


def _normalized(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def solve(grid):
    h, w = len(grid), len(grid[0])
    components = _components(grid)

    def yellow_cells(comp):
        return [(r, c) for r, c in comp if grid[r][c] == 4]

    def decoration_colors(comp):
        return {grid[r][c] for r, c in comp if grid[r][c] != 4}

    base = max(components, key=lambda comp: len(decoration_colors(comp)))
    base_yellow_abs = yellow_cells(base)
    base_r0 = min(r for r, _ in base_yellow_abs)
    base_c0 = min(c for _, c in base_yellow_abs)
    base_yellow = tuple(
        sorted((r - base_r0, c - base_c0) for r, c in base_yellow_abs)
    )
    base_decorations = tuple(
        (r - base_r0, c - base_c0, grid[r][c])
        for r, c in base
        if grid[r][c] != 4
    )

    transformed = []
    for index in range(8):
        raw_yellow = [_spin(point, index) for point in base_yellow]
        min_r = min(r for r, _ in raw_yellow)
        min_c = min(c for _, c in raw_yellow)
        shape = tuple(sorted((r - min_r, c - min_c) for r, c in raw_yellow))
        decorations = tuple(
            (
                _spin((r, c), index)[0] - min_r,
                _spin((r, c), index)[1] - min_c,
                value,
            )
            for r, c, value in base_decorations
        )
        transformed.append((shape, decorations))

    output = [row[:] for row in grid]
    for comp in components:
        if comp is base:
            continue
        target_yellow_abs = yellow_cells(comp)
        target_r0 = min(r for r, _ in target_yellow_abs)
        target_c0 = min(c for _, c in target_yellow_abs)
        target_shape = _normalized(target_yellow_abs)
        target_red = {
            (r - target_r0, c - target_c0)
            for r, c in comp
            if grid[r][c] == 2
        }

        chosen = None
        for shape, decorations in transformed:
            if shape != target_shape:
                continue
            transformed_red = {(r, c) for r, c, value in decorations if value == 2}
            if target_red and not (transformed_red & target_red):
                continue
            chosen = decorations
            break
        if chosen is None:
            continue

        for rel_r, rel_c, value in chosen:
            r, c = target_r0 + rel_r, target_c0 + rel_c
            if 0 <= r < h and 0 <= c < w:
                output[r][c] = value
    return output
