"""Visible-example solution for ARC task 03000b260ae0."""

DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid):
    """Nonzero 4-connected components in row-major/BFS order."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] == 0 or (r0, c0) in seen:
                continue
            queue = [(r0, c0)]
            seen.add((r0, c0))
            order = []
            cursor = 0
            while cursor < len(queue):
                r, c = queue[cursor]
                cursor += 1
                order.append((r, c))
                for dr, dc in DIRS4:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            grid[nr][nc] != 0 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(order)
    return result


def solve(grid):
    h, w = len(grid), len(grid[0])
    components = _components(grid)

    # The only multi-cell object is the stamp/template.  Isolated maroon cells
    # are placement markers.  When the template contains several maroon cells,
    # the visible examples select the last maroon cell in the component's BFS
    # traversal as the alignment anchor.
    template = next(
        comp for comp in components
        if len(comp) > 1 and any(grid[r][c] == 9 for r, c in comp)
    )
    markers = [
        comp[0] for comp in components
        if len(comp) == 1 and grid[comp[0][0]][comp[0][1]] == 9
    ]
    anchor = [(r, c) for r, c in template if grid[r][c] == 9][-1]

    counts = [[0 for _ in range(w)] for _ in range(h)]
    ar, ac = anchor
    for mr, mc in markers:
        for tr, tc in template:
            r, c = mr + tr - ar, mc + tc - ac
            if 0 <= r < h and 0 <= c < w:
                counts[r][c] += 1

    return [
        [0 if n == 0 else 2 if n == 1 else 3 if n == 2 else 4 for n in row]
        for row in counts
    ]
