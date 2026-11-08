"""Visible-example solution for the reviewer solve episode."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Extract the second-largest 4-connected color-2 component.

    The selected component is cropped to its bounding box; its cells become 8
    and every other cell in that crop becomes 0.
    """
    if not grid or not grid[0]:
        raise ValueError("grid must be non-empty")
    height, width = len(grid), len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] != 2 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = row + dr, col + dc
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and grid[nxt[0]][nxt[1]] == 2
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            components.append(cells)

    if len(components) < 2:
        raise ValueError("expected at least two color-2 components")

    # Visible examples have distinct component sizes.  The top-row key makes
    # the behavior deterministic should a tie appear.
    components.sort(key=lambda cells: (-len(cells), min(r for r, _ in cells)))
    selected = set(components[1])
    top = min(r for r, _ in selected)
    bottom = max(r for r, _ in selected)
    left = min(c for _, c in selected)
    right = max(c for _, c in selected)
    return [
        [8 if (row, col) in selected else 0 for col in range(left, right + 1)]
        for row in range(top, bottom + 1)
    ]
