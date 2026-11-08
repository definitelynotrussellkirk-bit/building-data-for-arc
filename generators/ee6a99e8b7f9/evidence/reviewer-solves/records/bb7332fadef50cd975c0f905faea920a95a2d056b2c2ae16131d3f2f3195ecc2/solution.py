from collections import deque


def solve(grid):
    """Transform the visible marker/rectangle construction.

    Color 9 markers sit immediately outside solid color-5 or color-6
    rectangles.  A 5-rectangle disappears while each incident marker is
    copied one cell onto its boundary.  A 6-rectangle remains while each
    incident marker moves inward to the middle cell along its entry ray
    (the farther of the two middle cells for an even thickness).
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]

    # Label each orthogonally connected 5/6 object in the untouched input.
    component_at = {}
    components = []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color not in (5, 6) or (r, c) in component_at:
                continue
            idx = len(components)
            queue = deque([(r, c)])
            component_at[(r, c)] = idx
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in component_at
                    ):
                        component_at[(nr, nc)] = idx
                        queue.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            components.append(
                {
                    "color": color,
                    "cells": cells,
                    "r0": min(rows),
                    "r1": max(rows),
                    "c0": min(cols),
                    "c1": max(cols),
                }
            )

    # A color-5 object is transparent in the result except for copied marker
    # cells on the boundary.
    for comp in components:
        if comp["color"] == 5:
            for r, c in comp["cells"]:
                out[r][c] = 8

    # Determine every marker action from the original grid, not the partially
    # transformed output.
    for r in range(height):
        for c in range(width):
            if grid[r][c] != 9:
                continue
            incident = []
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                idx = component_at.get((nr, nc))
                if idx is not None:
                    incident.append((idx, dr, dc, nr, nc))

            # All visible examples give each marker one incident rectangle.
            # Leaving an unrelated 9 untouched is safer than deleting it.
            for idx, dr, dc, nr, nc in incident:
                comp = components[idx]
                if comp["color"] == 5:
                    # Retain the outside marker and copy it onto the first cell.
                    out[nr][nc] = 9
                else:
                    # Remove the outside marker and move to the central depth.
                    out[r][c] = 8
                    thickness = (
                        comp["r1"] - comp["r0"] + 1
                        if dr
                        else comp["c1"] - comp["c0"] + 1
                    )
                    steps = thickness // 2 + 1
                    tr, tc = r + dr * steps, c + dc * steps
                    out[tr][tc] = 9

    return out
