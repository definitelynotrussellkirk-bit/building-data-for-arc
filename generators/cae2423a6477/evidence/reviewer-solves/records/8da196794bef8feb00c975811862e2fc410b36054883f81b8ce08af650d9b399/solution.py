def solve(grid):
    """Recolor the unique hollow rectangular frame from green (3) to orange (7)."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]
    seen = set()

    for r0 in range(height):
        for c0 in range(width):
            if grid[r0][c0] != 3 or (r0, c0) in seen:
                continue

            stack = [(r0, c0)]
            seen.add((r0, c0))
            component = []
            while stack:
                r, c = stack.pop()
                component.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 3
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            rows = [r for r, _ in component]
            cols = [c for _, c in component]
            r1, r2 = min(rows), max(rows)
            c1, c2 = min(cols), max(cols)
            box_h, box_w = r2 - r1 + 1, c2 - c1 + 1
            if box_h < 3 or box_w < 3:
                continue

            expected_border = {
                (r, c)
                for r in range(r1, r2 + 1)
                for c in range(c1, c2 + 1)
                if r in (r1, r2) or c in (c1, c2)
            }
            if set(component) == expected_border:
                for r, c in component:
                    out[r][c] = 7

    return out
