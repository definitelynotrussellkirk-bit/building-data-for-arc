"""Visible-example solution for the prepared reviewer episode."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Keep the largest 4-connected object of each nonzero color."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen: set[tuple[int, int]] = set()
    by_color: dict[int, list[list[tuple[int, int]]]] = {}

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            component: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                component.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            by_color.setdefault(color, []).append(component)

    for color, components in by_color.items():
        # Visible examples have a unique maximum. The coordinate tie-break is
        # deterministic without inventing extra cells if an unseen tie occurs.
        chosen = min(
            components,
            key=lambda cells: (-len(cells), min(cells)),
        )
        for row, col in chosen:
            output[row][col] = color
    return output
