from collections import deque


def _components(grid):
    """Return 4-connected components of non-background cells."""
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    seen = set()

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            component = set()
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                cr, cc = queue.popleft()
                component.add((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < rows
                        and 0 <= nc < cols
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            yield component


def _encloses_hole(component):
    """Whether a component surrounds any cell under 4-connectivity."""
    min_r = min(r for r, _ in component)
    max_r = max(r for r, _ in component)
    min_c = min(c for _, c in component)
    max_c = max(c for _, c in component)

    # Add a one-cell exterior frame. Flood all cells that can reach that frame
    # without crossing the component. Any remaining cell is enclosed.
    top, bottom = min_r - 1, max_r + 1
    left, right = min_c - 1, max_c + 1
    start = (top, left)
    exterior = {start}
    queue = deque([start])

    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            nxt = (nr, nc)
            if not (top <= nr <= bottom and left <= nc <= right):
                continue
            if nxt in component or nxt in exterior:
                continue
            exterior.add(nxt)
            queue.append(nxt)

    for r in range(min_r, max_r + 1):
        for c in range(min_c, max_c + 1):
            if (r, c) not in component and (r, c) not in exterior:
                return True
    return False


def solve(grid):
    """Color hole-containing objects 8 and all other objects 4."""
    output = [row[:] for row in grid]
    for component in _components(grid):
        color = 8 if _encloses_hole(component) else 4
        for r, c in component:
            output[r][c] = color
    return output
