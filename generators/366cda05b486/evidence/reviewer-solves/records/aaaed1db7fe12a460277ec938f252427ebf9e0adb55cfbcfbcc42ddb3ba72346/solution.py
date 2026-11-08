"""Visible-example solution: extract the cardinal foreground cluster containing 1."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    seed = next((r, c) for r, row in enumerate(grid)
                for c, color in enumerate(row) if color == 1)
    cells = {seed}
    pending = [seed]
    while pending:
        r, c = pending.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if (0 <= nr < height and 0 <= nc < width
                    and grid[nr][nc] != 0 and (nr, nc) not in cells):
                cells.add((nr, nc))
                pending.append((nr, nc))
    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells)
    right = max(c for _, c in cells)
    return [[8 if (r, c) in cells else 0
             for c in range(left, right + 1)]
            for r in range(top, bottom + 1)]
