"""Standalone solution inferred/checked from the visible cross examples."""
from collections import Counter


def solve(grid):
    h, w = len(grid), len(grid[0])
    background = Counter(v for row in grid[1:-1] for v in row[1:-1]).most_common(1)[0][0]
    out = [list(row) for row in grid]
    occupied = {(r, c) for r in range(1, h - 1) for c in range(1, w - 1)
                if grid[r][c] != background}
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))
    while occupied:
        start = min(occupied)
        color = grid[start[0]][start[1]]
        pending, cells = [start], set()
        occupied.remove(start)
        while pending:
            r, c = pending.pop()
            cells.add((r, c))
            for dr, dc in directions:
                neighbor = (r + dr, c + dc)
                if neighbor in occupied and grid[neighbor[0]][neighbor[1]] == color:
                    occupied.remove(neighbor)
                    pending.append(neighbor)
        centers = [(r, c) for r, c in cells
                   if all((r + dr, c + dc) in cells for dr, dc in directions)]
        if len(centers) != 1:
            raise ValueError("Expected one four-neighbor center per colored cross")
        r, c = centers[0]
        lengths = []
        for dr, dc in directions:
            n = 0
            while (r + dr * (n + 1), c + dc * (n + 1)) in cells:
                n += 1
            lengths.append(n)
        longest = max(lengths)
        if lengths.count(longest) != 1:
            raise ValueError("Expected one longest arm")
        dr, dc = directions[lengths.index(longest)]
        if dr:
            facing, opposite = ((0, c), (h - 1, c)) if dr < 0 else ((h - 1, c), (0, c))
        else:
            facing, opposite = ((r, 0), (r, w - 1)) if dc < 0 else ((r, w - 1), (r, 0))
        out[facing[0]][facing[1]] = 0
        out[opposite[0]][opposite[1]] = color
    return out
