def solve(grid):
    if not grid:
        return []
    height, width = len(grid), len(grid[0])
    steps = ((-1, 0), (1, 0), (0, -1), (0, 1))
    owner = [[-1] * width for _ in range(height)]
    components = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 0 or owner[r][c] >= 0:
                continue
            component_id = len(components)
            color = grid[r][c]
            owner[r][c] = component_id
            pending = [(r, c)]
            cells = []
            while pending:
                rr, cc = pending.pop()
                cells.append((rr, cc))
                for dr, dc in steps:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and owner[nr][nc] < 0 and grid[nr][nc] == color):
                        owner[nr][nc] = component_id
                        pending.append((nr, nc))
            components.append(cells)
    answer = [list(row) for row in grid]
    for component_id, cells in enumerate(components):
        adjacent = set()
        for r, c in cells:
            for dr, dc in steps:
                nr, nc = r + dr, c + dc
                if 0 <= nr < height and 0 <= nc < width:
                    other = owner[nr][nc]
                    if other >= 0 and other != component_id:
                        adjacent.add(other)
        if len(adjacent) == 1:
            for r, c in cells:
                answer[r][c] = 8
    return answer
