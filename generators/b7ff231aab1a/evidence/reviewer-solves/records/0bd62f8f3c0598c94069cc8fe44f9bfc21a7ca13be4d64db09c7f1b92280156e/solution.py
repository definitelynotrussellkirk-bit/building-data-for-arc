def solve(grid):
    """Select by marker count and component area, then crop/scale/recolor."""
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []

    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp = []
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(comp)

    components.sort(
        key=lambda comp: (
            len(comp),
            min(r for r, _ in comp),
            min(c for _, c in comp),
        )
    )
    marker_count = sum(value == 9 for row in grid for value in row)
    chosen = components[marker_count - 1]

    top = min(r for r, _ in chosen)
    bottom = max(r for r, _ in chosen)
    left = min(c for _, c in chosen)
    right = max(c for _, c in chosen)
    crop = [row[left : right + 1] for row in grid[top : bottom + 1]]

    return [
        [8 if crop[r // 2][c // 2] != 0 else 0 for c in range(2 * len(crop[0]))]
        for r in range(2 * len(crop))
    ]
