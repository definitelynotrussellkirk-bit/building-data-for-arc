"""Visible-example solution for ARC task 7b8cb193f82c."""
from __future__ import annotations

from collections import deque
from copy import deepcopy


def solve(grid):
    """Paint each enclosed zero region in alternating inward rings 2,3,2,3..."""
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0}
    neighbors = ((-1, 0), (1, 0), (0, -1), (0, 1))

    while unseen:
        start = next(iter(unseen))
        component = {start}
        queue = [start]
        unseen.remove(start)
        touches_border = False
        while queue:
            r, c = queue.pop()
            if r in (0, h - 1) or c in (0, w - 1):
                touches_border = True
            for dr, dc in neighbors:
                rr, cc = r + dr, c + dc
                if (rr, cc) in unseen:
                    unseen.remove((rr, cc))
                    component.add((rr, cc))
                    queue.append((rr, cc))

        if touches_border:
            continue

        # Multi-source BFS from the component boundary gives inward layer depth.
        frontier = deque()
        depth = {}
        for r, c in component:
            if any((r + dr, c + dc) not in component for dr, dc in neighbors):
                depth[(r, c)] = 1
                frontier.append((r, c))
        while frontier:
            r, c = frontier.popleft()
            for dr, dc in neighbors:
                nxt = (r + dr, c + dc)
                if nxt in component and nxt not in depth:
                    depth[nxt] = depth[(r, c)] + 1
                    frontier.append(nxt)
        for (r, c), layer in depth.items():
            out[r][c] = 2 if layer % 2 else 3

    return out
