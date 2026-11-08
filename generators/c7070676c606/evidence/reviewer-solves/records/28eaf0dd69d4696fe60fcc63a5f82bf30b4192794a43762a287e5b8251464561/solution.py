def solve(grid):
    """Recolor the ranked four-connected green object selected by top-row blue count."""
    result = [list(row) for row in grid]
    if not grid or not grid[0]:
        return result

    rank = sum(value == 1 for value in grid[0])
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 3
    }
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        cells = [start]
        pending = [start]
        while pending:
            r, c = pending.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    pending.append(neighbor)
                    cells.append(neighbor)
        components.append(cells)

    components.sort(key=lambda cells: (-len(cells), min(cells)))
    if 1 <= rank <= len(components):
        for r, c in components[rank - 1]:
            result[r][c] = 2
    return result
