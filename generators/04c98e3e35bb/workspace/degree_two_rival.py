def solve(grid):
    """Recolor occupancy using the degree-two chains seen in the examples."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    occupied = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}

    counts = {}
    for r, c in occupied:
        counts[grid[r][c]] = counts.get(grid[r][c], 0) + 1
    structural = {(r, c) for r, c in occupied if counts[grid[r][c]] > 1}

    def neighbors(cell):
        r, c = cell
        return {(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)} & structural

    degree_two = {cell for cell in structural if len(neighbors(cell)) == 2}
    unseen = set(degree_two)
    red = set()
    while unseen:
        start = unseen.pop()
        component = {start}
        pending = [start]
        while pending:
            cell = pending.pop()
            for other in neighbors(cell) & unseen:
                unseen.remove(other)
                component.add(other)
                pending.append(other)
        if len(component) == 3:
            red.update(component)

    return [[0 if (r, c) not in occupied else 2 if (r, c) in red else 8
             for c in range(w)] for r in range(h)]
