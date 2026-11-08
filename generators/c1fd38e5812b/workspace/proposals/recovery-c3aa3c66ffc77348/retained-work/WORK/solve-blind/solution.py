"""Blind solution for task 4201f3b3ea1b, derived only from visible grids."""
from __future__ import annotations


def _components(cells):
    remaining = set(cells)
    result = []
    while remaining:
        seed = remaining.pop()
        component = {seed}
        frontier = [seed]
        while frontier:
            r, c = frontier.pop()
            neighbors = {
                point
                for point in remaining
                if max(abs(point[0] - r), abs(point[1] - c)) <= 2
            }
            remaining -= neighbors
            component |= neighbors
            frontier.extend(neighbors)
        result.append(component)
    return result


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    motif_cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 6)
    }
    components = _components(motif_cells)
    candidates = [
        component
        for component in components
        if any(grid[r][c] == 5 for r, c in component)
    ]
    if not candidates:
        return [row[:] for row in grid]
    component = max(
        candidates,
        key=lambda comp: (
            sum(grid[r][c] != 5 for r, c in comp),
            len(comp),
        ),
    )
    anchors = sorted((r, c) for r, c in component if grid[r][c] == 5)
    anchor_r, anchor_c = anchors[0]
    motif = [
        (r - anchor_r, c - anchor_c, grid[r][c])
        for r, c in sorted(component)
    ]

    result = [row[:] for row in grid]
    targets = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 6
    ]
    for target_r, target_c in targets:
        for dr, dc, value in motif:
            r, c = target_r + dr, target_c + dc
            if 0 <= r < height and 0 <= c < width:
                result[r][c] = value
    return result
