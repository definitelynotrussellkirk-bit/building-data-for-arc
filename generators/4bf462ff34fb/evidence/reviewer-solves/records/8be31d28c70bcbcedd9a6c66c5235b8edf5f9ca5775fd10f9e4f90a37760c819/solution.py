from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Recolor blue components that touch only the top border from 1 to 3."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [row[:] for row in grid]
    seen: set[tuple[int, int]] = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            component: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                component.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            touches_top = any(rr == 0 for rr, _ in component)
            touches_other_border = any(
                rr == height - 1 or cc == 0 or cc == width - 1
                for rr, cc in component
            )
            if touches_top and not touches_other_border:
                for rr, cc in component:
                    output[rr][cc] = 3

    return output
