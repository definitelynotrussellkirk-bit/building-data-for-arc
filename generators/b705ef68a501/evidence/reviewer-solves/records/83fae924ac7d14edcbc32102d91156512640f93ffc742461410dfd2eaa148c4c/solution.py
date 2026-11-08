from collections import deque


def solve(grid):
    """Return the lowest non-background object aligned with a top-row marker."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    marker_columns = {c for c, value in enumerate(grid[0]) if value != 0}

    seen = set()
    components = []
    for r in range(1, height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue

            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                cr, cc = queue.popleft()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if not (1 <= nr < height and 0 <= nc < width):
                        continue
                    if (nr, nc) in seen or grid[nr][nc] != color:
                        continue
                    seen.add((nr, nc))
                    queue.append((nr, nc))

            if any(c in marker_columns for _, c in cells):
                rows = [r for r, _ in cells]
                cols = [c for _, c in cells]
                components.append(
                    {
                        "color": color,
                        "cells": cells,
                        "top": min(rows),
                        "bottom": max(rows),
                        "left": min(cols),
                        "right": max(cols),
                        "marker_overlap": len({c for _, c in cells} & marker_columns),
                    }
                )

    if not components:
        return []

    # "Lowest" is the observed discriminator.  The remaining keys only make
    # an otherwise unspecified tie deterministic.
    chosen = max(
        components,
        key=lambda obj: (
            obj["bottom"],
            obj["top"],
            obj["marker_overlap"],
            len(obj["cells"]),
            obj["left"],
        ),
    )

    out_height = chosen["bottom"] - chosen["top"] + 1
    out_width = chosen["right"] - chosen["left"] + 1
    output = [[0 for _ in range(out_width)] for _ in range(out_height)]
    for r, c in chosen["cells"]:
        output[r - chosen["top"]][c - chosen["left"]] = chosen["color"]
    return output
