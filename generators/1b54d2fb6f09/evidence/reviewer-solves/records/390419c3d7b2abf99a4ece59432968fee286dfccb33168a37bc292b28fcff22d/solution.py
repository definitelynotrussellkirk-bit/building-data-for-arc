def solve(grid):
    """Recolor endpoints of straight red components, leaving all else fixed."""
    out = [row[:] for row in grid]
    h = len(grid)
    w = len(grid[0]) if h else 0
    unseen = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 2
    }
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    while unseen:
        start = next(iter(unseen))
        unseen.remove(start)
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in directions:
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    component.add(nxt)
                    stack.append(nxt)

        if len(component) < 2:
            continue
        rows = {r for r, _ in component}
        cols = {c for _, c in component}
        if len(rows) == 1:
            r = next(iter(rows))
            lo, hi = min(cols), max(cols)
            if len(component) == hi - lo + 1:
                out[r][lo] = 8
                out[r][hi] = 8
        elif len(cols) == 1:
            c = next(iter(cols))
            lo, hi = min(rows), max(rows)
            if len(component) == hi - lo + 1:
                out[lo][c] = 8
                out[hi][c] = 8

    return out
