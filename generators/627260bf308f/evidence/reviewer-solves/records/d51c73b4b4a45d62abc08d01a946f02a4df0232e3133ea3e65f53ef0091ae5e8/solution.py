"""Visible-example component-size recoloring candidate; no answer lookup."""
from collections import deque


def components(grid, diagonal=False):
    remaining = {(r,c) for r,row in enumerate(grid[1:],1)
                 for c,value in enumerate(row) if value == 8}
    directions = [(1,0),(-1,0),(0,1),(0,-1)]
    if diagonal:
        directions += [(1,1),(1,-1),(-1,1),(-1,-1)]
    groups = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        group = {first}
        queue = deque([first])
        while queue:
            r,c = queue.popleft()
            for dr,dc in directions:
                other = (r+dr,c+dc)
                if other in remaining:
                    remaining.remove(other)
                    group.add(other)
                    queue.append(other)
        groups.append(group)
    return groups


def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected a nonempty rectangular grid')
    palette = [color for color in grid[0] if color != 0]
    groups = components(grid)
    if len(groups) != len(palette):
        raise ValueError('Expected one palette entry per body component')
    # Equal-size components are not established by these demonstrations.
    # A stable bounding-box order makes this candidate deterministic.
    def key(group):
        rows = [r for r,c in group]
        cols = [c for r,c in group]
        return len(group), min(rows), min(cols), max(rows), max(cols)
    result = [list(row) for row in grid]
    for color,group in zip(palette,sorted(groups,key=key)):
        for r,c in group:
            result[r][c] = color
    return result
