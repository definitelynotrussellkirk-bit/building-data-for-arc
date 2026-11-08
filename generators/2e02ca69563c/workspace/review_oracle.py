"""Independent Python test oracle. Training labels remain the Racket authority.

This file is intentionally outside generator.py. It imports no generator code.
"""
from collections import defaultdict


def components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c]}
    while unseen:
        point = min(unseen)
        color = grid[point[0]][point[1]]
        stack, cells = [point], set()
        unseen.remove(point)
        while stack:
            r, c = stack.pop()
            cells.add((r, c))
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in unseen and grid[p[0]][p[1]] == color:
                    unseen.remove(p)
                    stack.append(p)
        yield color, cells


def frames(grid):
    found = []
    for color, cells in components(grid):
        top = min(r for r,c in cells); bottom = max(r for r,c in cells)
        left = min(c for r,c in cells); right = max(c for r,c in cells)
        if bottom-top < 2 or right-left < 2:
            continue
        border = {(r,c) for r in range(top,bottom+1) for c in range(left,right+1)
                  if r in (top,bottom) or c in (left,right)}
        if cells == border:
            found.append((top,left,bottom,right,color))
    return sorted(found)


def groups(grid, frame):
    top,left,bottom,right,border_color = frame
    out = defaultdict(list)
    for r in range(top+1,bottom):
        for c in range(left+1,right):
            if grid[r][c] not in (0,border_color):
                out[grid[r][c]].append((r,c))
    return dict(out)


def path(points):
    (r0,c0),(r1,c1) = sorted(points)
    horizontal = [(r0,c) for c in range(min(c0,c1),max(c0,c1)+1)]
    vertical = [(r,c1) for r in range(r0,r1+1)]
    return set(horizontal+vertical)


def solve_reference(grid):
    """Row-major first endpoint, then horizontal, then vertical; local counts."""
    out = [list(row) for row in grid]
    for frame in frames(grid):
        for color, points in groups(grid,frame).items():
            if len(points) == 2:
                for r,c in path(points):
                    out[r][c] = color
    return out


def path_conflicts(grid):
    problems = []
    reserved = {}
    for frame in frames(grid):
        for color, points in groups(grid,frame).items():
            if len(points) != 2:
                continue
            for p in path(points):
                value = grid[p[0]][p[1]]
                if value not in (0,color):
                    problems.append({'kind':'endpoint_overwrite','cell':p,'color':color,'old':value})
                if p in reserved and reserved[p] != color:
                    problems.append({'kind':'route_crossing','cell':p,'colors':[reserved[p],color]})
                reserved[p] = color
    return problems


def hand_witness():
    grid = [[0]*13 for _ in range(9)]
    for left in (1,7):
        for r in range(1,6):
            for c in range(left,left+5):
                if r in (1,5) or c in (left,left+4):
                    grid[r][c] = 8
        grid[2][left+1] = grid[4][left+3] = 2
    return grid
