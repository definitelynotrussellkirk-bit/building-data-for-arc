"""Standalone program inferred from the three visible examples."""
from collections import Counter


def solve(grid):
    height, width = len(grid), len(grid[0])
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    pending = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
               if value != background}
    objects = []
    while pending:
        start = min(pending)
        pending.remove(start)
        component = {start}
        frontier = [start]
        color = grid[start[0]][start[1]]
        while frontier:
            r, c = frontier.pop()
            for next_cell in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if next_cell in pending and grid[next_cell[0]][next_cell[1]] == color:
                    pending.remove(next_cell)
                    component.add(next_cell)
                    frontier.append(next_cell)
        objects.append(component)
    output = [[background] * width for _ in range(height)]
    for component in objects:
        # In a connected undirected pixel graph, a cycle exists iff E >= V.
        edges = sum((r+1, c) in component for r, c in component)
        edges += sum((r, c+1) in component for r, c in component)
        closed = edges >= len(component)
        left = min(c for _, c in component)
        right = max(c for _, c in component)
        shift = -left if closed else width - 1 - right
        target_color = 2 if closed else 3
        for r, c in component:
            output[r][c + shift] = target_color
    return output
