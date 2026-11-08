"""Visible-example solution for the prepared post-repair episode."""


def _five_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 5 or (r, c) in seen:
                continue
            seen.add((r, c))
            stack = [(r, c)]
            component = []
            while stack:
                pr, pc = stack.pop()
                component.append((pr, pc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = pr + dr, pc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 5
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(component)
    return components


def solve(grid):
    out = [[0 for _ in row] for row in grid]
    for component in _five_components(grid):
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        r0, c0, r1, c1 = min(rows), min(cols), max(rows), max(cols)

        # The examples treat each 5-component's bounding box as a box and
        # restore its complete border, even when a colored cell replaced 5.
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if r in (r0, r1) or c in (c0, c1):
                    out[r][c] = 5

        # Within each interior column, retain nonzero order and pack downward.
        for c in range(c0 + 1, c1):
            values = [grid[r][c] for r in range(r0 + 1, r1) if grid[r][c] != 0]
            start = r1 - len(values)
            for offset, value in enumerate(values):
                out[start + offset][c] = value
    return out
