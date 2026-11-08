from collections import deque


def _one_components(grid):
    """Return 4-connected components of the color-1 frame cells."""
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            component = []
            while queue:
                rr, cc = queue.popleft()
                component.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(component)
    return components


def solve(grid):
    """Fill each 1-bordered rectangle with its alternating two-color motif."""
    out = [row[:] for row in grid]

    for component in _one_components(grid):
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)

        # Only treat a component as a complete rectangular frame.
        if bottom - top < 2 or right - left < 2:
            continue
        perimeter = {
            (r, c)
            for r in range(top, bottom + 1)
            for c in range(left, right + 1)
            if r in (top, bottom) or c in (left, right)
        }
        if set(component) != perimeter:
            continue

        seeds = [
            (r, c, grid[r][c])
            for r in range(top + 1, bottom)
            for c in range(left + 1, right)
            if grid[r][c] not in (0, 1)
        ]
        if len(seeds) != 2:
            continue

        # The demonstrations place the two motif colors left-to-right in the
        # first interior row.  Repeat them across every interior row.
        seeds.sort(key=lambda item: (item[1], item[0]))
        first, second = seeds[0][2], seeds[1][2]
        for r in range(top + 1, bottom):
            for offset, c in enumerate(range(left + 1, right)):
                out[r][c] = first if offset % 2 == 0 else second

    return out
