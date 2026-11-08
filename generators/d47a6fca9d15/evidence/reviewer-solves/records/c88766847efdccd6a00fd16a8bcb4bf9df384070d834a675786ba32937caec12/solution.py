"""Infer component size ranks from the visible demonstrations only."""


def solve(grid):
    result = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            todo = [(row, col)]
            seen.add((row, col))
            component = []
            while todo:
                r, c = todo.pop()
                component.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and grid[nr][nc] != 0 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            components.append(component)
    sizes = sorted({len(component) for component in components})
    colors = dict(zip(sizes, (2, 4, 6)))
    if len(sizes) != 3:
        raise ValueError('Visible examples support exactly three size ranks')
    for component in components:
        for r, c in component:
            result[r][c] = colors[len(component)]
    return result
