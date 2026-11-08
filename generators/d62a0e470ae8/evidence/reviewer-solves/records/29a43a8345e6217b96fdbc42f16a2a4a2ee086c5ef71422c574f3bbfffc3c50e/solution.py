def solve(grid):
    marker = grid[0][0]
    h, w = len(grid), len(grid[0])
    remaining = {(r,c) for r in range(h) for c in range(w)
                 if grid[r][c] != 0 and (r,c) != (0,0)}
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        color = grid[start[0]][start[1]]
        component = {start}
        stack = [start]
        while stack:
            r,c = stack.pop()
            for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if q in remaining and grid[q[0]][q[1]] == color:
                    remaining.remove(q)
                    component.add(q)
                    stack.append(q)
        components.append(component)
    if not components:
        return [[0]]
    component = max(components, key=len)
    r0, r1 = min(r for r,c in component), max(r for r,c in component)
    c0, c1 = min(c for r,c in component), max(c for r,c in component)
    crop = [[grid[r][c] if (r,c) in component else 0
             for c in range(c0,c1+1)] for r in range(r0,r1+1)]
    if marker == 1:
        return [list(row) for row in zip(*crop[::-1])]
    if marker == 2:
        return [row[::-1] for row in crop]
    if marker == 3:
        return crop[::-1]
    if marker == 4:
        return [row[::-1] for row in crop[::-1]]
    raise ValueError('Unobserved marker: %r' % marker)
