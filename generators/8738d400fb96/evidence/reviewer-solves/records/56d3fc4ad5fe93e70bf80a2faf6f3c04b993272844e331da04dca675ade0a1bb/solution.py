def solve(grid):
    """Move the largest orthogonal color-3 object by the 2-to-1 vector."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0] * width for _ in range(height)]
    markers = {}
    remaining = set()
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color in (1, 2):
                markers[color] = (r, c)
            elif color == 3:
                remaining.add((r, c))
    components = []
    while remaining:
        seed = min(remaining)
        remaining.remove(seed)
        component = {seed}
        pending = [seed]
        while pending:
            r, c = pending.pop()
            for neighbor in ((r - 1, c), (r + 1, c),
                             (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    pending.append(neighbor)
        components.append(component)
    if not components or 1 not in markers or 2 not in markers:
        return output
    main = max(components, key=len)
    dr = markers[1][0] - markers[2][0]
    dc = markers[1][1] - markers[2][1]
    for r, c in main:
        nr, nc = r + dr, c + dc
        if 0 <= nr < height and 0 <= nc < width:
            output[nr][nc] = 8
    return output
