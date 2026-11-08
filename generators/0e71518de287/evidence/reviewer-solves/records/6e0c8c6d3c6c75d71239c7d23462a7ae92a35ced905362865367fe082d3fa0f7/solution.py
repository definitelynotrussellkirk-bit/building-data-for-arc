def solve(grid):
    """Fill the hollow 4-frame indicated by the lone colored marker."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    markers = [
        (r, c, grid[r][c])
        for r in range(height)
        for c in range(width)
        if grid[r][c] not in (0, 4)
    ]
    if not markers:
        return out

    # The visible tasks contain one marker; retaining all marker cells makes the
    # target selection deterministic even if a future instance repeats its color.
    marker_cells = [(r, c) for r, c, _ in markers]
    marker_color = markers[0][2]

    seen = set()
    components = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] != 4 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            component = []
            while stack:
                cr, cc = stack.pop()
                component.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 4
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(component)

    if not components:
        return out

    def marker_distance(component):
        return min(
            abs(mr - r) + abs(mc - c)
            for mr, mc in marker_cells
            for r, c in component
        )

    target = min(components, key=marker_distance)
    rows = [r for r, _ in target]
    cols = [c for _, c in target]
    top, bottom = min(rows), max(rows)
    left, right = min(cols), max(cols)

    for r in range(top + 1, bottom):
        for c in range(left + 1, right):
            if out[r][c] == 0:
                out[r][c] = marker_color
    return out
