from collections import Counter, defaultdict


def _components(grid, background):
    """Return 4-connected, same-colour non-background components."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            colour = grid[row][col]
            if colour == background or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == colour
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            components.append(
                {
                    "colour": colour,
                    "cells": cells,
                    "top": min(rows),
                    "bottom": max(rows),
                    "left": min(cols),
                    "right": max(cols),
                }
            )

    return components


def solve(grid):
    """Extract the small four-unit-wide motif selected by the composition."""
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    components = _components(grid, background)

    singleton_colours = defaultdict(int)
    for component in components:
        if len(component["cells"]) == 1:
            singleton_colours[component["colour"]] += 1

    candidates = []
    for component in components:
        if len(component["cells"]) <= 1:
            continue
        height = component["bottom"] - component["top"] + 1
        width = component["right"] - component["left"] + 1

        # Across all visible examples the wanted motif is the only compact
        # non-square object with a four-cell long side.  The selected colour
        # also has an isolated swatch when two copies of the motif are present.
        if max(height, width) != 4 or min(height, width) < 2:
            continue

        foreign = 0
        for row in range(component["top"], component["bottom"] + 1):
            for col in range(component["left"], component["right"] + 1):
                value = grid[row][col]
                if value not in (background, component["colour"]):
                    foreign += 1

        candidates.append(
            (
                1 if singleton_colours[component["colour"]] else 0,
                1 if foreign else 0,
                foreign,
                component["top"],
                component,
            )
        )

    if not candidates:
        raise ValueError("No compact four-unit motif found")

    # Prefer the colour identified by an isolated swatch, then the copy that
    # contains the payload colour.  Row order is only a deterministic fallback.
    component = max(candidates, key=lambda item: item[:-1])[-1]
    return [
        row[component["left"] : component["right"] + 1]
        for row in grid[component["top"] : component["bottom"] + 1]
    ]
