from __future__ import annotations


def solve(grid):
    """Recolor below-header components by descending area rank."""
    out = [list(row) for row in grid]
    legend = [value for value in grid[0] if value != 0]
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(1, h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (1 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)

    components.sort(
        key=lambda cells: (
            -len(cells),
            min(r for r, _ in cells),
            min(c for _, c in cells),
        )
    )
    for color, cells in zip(legend, components):
        for r, c in cells:
            out[r][c] = color
    return out
