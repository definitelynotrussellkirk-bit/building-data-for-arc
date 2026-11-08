"""Visible-example solution for 529bd4803bcc."""


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [[5 if grid[r][c] == 5 else 0 for c in range(width)] for r in range(height)]
    unseen = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] != 5
    }
    while unseen:
        start = unseen.pop()
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in unseen:
                    unseen.remove((nr, nc))
                    component.add((nr, nc))
                    stack.append((nr, nc))
        seeds = [grid[r][c] for r, c in component if grid[r][c] in (1, 2, 3)]
        if len(seeds) == 1:
            color = seeds[0]
            for r, c in component:
                out[r][c] = color
    return out
