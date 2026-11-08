from __future__ import annotations


def _components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[list[tuple[int, int]]] = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] != color or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            component: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                component.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            found.append(component)
    return found


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill the interiors of complete orange rectangular outlines with cyan."""
    out = [row[:] for row in grid]
    for component in _components(grid, 7):
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(cols), max(cols)
        if r1 - r0 < 2 or c1 - c0 < 2:
            continue

        expected_border = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if set(component) != expected_border:
            continue

        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                if grid[r][c] == 0:
                    out[r][c] = 8
    return out
