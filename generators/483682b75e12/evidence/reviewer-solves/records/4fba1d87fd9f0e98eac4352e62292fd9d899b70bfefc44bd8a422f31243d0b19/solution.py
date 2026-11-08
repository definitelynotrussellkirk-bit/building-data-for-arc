from collections import Counter, deque


def solve(grid):
    """Move each colored object upward by its number of cells.

    The dominant color is the background.  A full-width uniform bottom row is a
    fixed floor and is not treated as a movable object.  Movable objects are
    4-connected components of a single non-background color.
    """
    h = len(grid)
    w = len(grid[0]) if h else 0
    if not h or not w:
        return [row[:] for row in grid]

    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    floor_row = None
    if len(set(grid[-1])) == 1 and grid[-1][0] != background:
        floor_row = h - 1

    out = [row[:] for row in grid]
    movable = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] != background and r != floor_row
    }

    # Remove the original objects before placing their translated copies.
    for r, c in movable:
        out[r][c] = background

    seen = set()
    for start in sorted(movable):
        if start in seen:
            continue
        color = grid[start[0]][start[1]]
        component = []
        queue = deque([start])
        seen.add(start)
        while queue:
            r, c = queue.popleft()
            component.append((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if (
                    (nr, nc) in movable
                    and (nr, nc) not in seen
                    and grid[nr][nc] == color
                ):
                    seen.add((nr, nc))
                    queue.append((nr, nc))

        shift = len(component)
        for r, c in component:
            nr = r - shift
            if 0 <= nr < h:
                out[nr][c] = color

    return out
