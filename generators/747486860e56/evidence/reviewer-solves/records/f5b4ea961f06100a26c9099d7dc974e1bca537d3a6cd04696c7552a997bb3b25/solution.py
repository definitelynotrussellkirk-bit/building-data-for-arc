from collections import Counter, deque


def _components(grid):
    """Return 8-connected components of nonzero cells in row-major order."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            comp = []
            while q:
                rr, cc = q.popleft()
                comp.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == dc == 0:
                            continue
                        nr, nc = rr + dr, cc + dc
                        if (
                            0 <= nr < h
                            and 0 <= nc < w
                            and grid[nr][nc] != 0
                            and (nr, nc) not in seen
                        ):
                            seen.add((nr, nc))
                            q.append((nr, nc))
            components.append(comp)
    return components


def solve(grid):
    h = len(grid)
    if h == 0:
        return []
    w = len(grid[0])

    components = _components(grid)
    if not components:
        return [row[:] for row in grid]

    # The large connected figure is retained.  Every other colored cell is a
    # marker that votes for the triangle color and determines its size.
    main = max(components, key=len)
    main_cells = set(main)
    markers = [
        (r, c, grid[r][c])
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0 and (r, c) not in main_cells
    ]
    if not markers:
        return [row[:] for row in grid]

    counts = Counter(color for _, _, color in markers)
    top_count = max(counts.values())
    tied = {color for color, count in counts.items() if count == top_count}
    # The examples resolve a frequency tie by the first tied color encountered
    # in row-major order.
    triangle_color = next(color for _, _, color in markers if color in tied)

    corner_to_dist = {
        (0, 0): lambda r, c: r + c,
        (0, w - 1): lambda r, c: r + (w - 1 - c),
        (h - 1, 0): lambda r, c: (h - 1 - r) + c,
        (h - 1, w - 1): lambda r, c: (h - 1 - r) + (w - 1 - c),
    }
    marker_positions = {(r, c) for r, c, _ in markers}
    corner = next(pos for pos in corner_to_dist if pos in marker_positions)

    result = [[0] * w for _ in range(h)]
    for r, c in main_cells:
        result[r][c] = grid[r][c]

    side = len(markers) - 1
    distance = corner_to_dist[corner]
    for r in range(h):
        for c in range(w):
            if distance(r, c) < side:
                result[r][c] = triangle_color

    return result
