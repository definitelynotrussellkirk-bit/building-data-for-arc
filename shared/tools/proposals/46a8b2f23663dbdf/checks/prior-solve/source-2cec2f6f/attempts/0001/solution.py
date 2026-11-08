"""Visible-example solution using connected components of the zero cells."""

def solve(grid):
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 0}
    while unseen:
        start = unseen.pop()
        component = [start]
        stack = [start]
        reaches_edge = False
        while stack:
            r, c = stack.pop()
            if r == 0 or c == 0 or r == height - 1 or c == width - 1:
                reaches_edge = True
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.append(neighbor)
                    stack.append(neighbor)
        fill = 3 if reaches_edge else 2
        for r, c in component:
            output[r][c] = fill
    return output
