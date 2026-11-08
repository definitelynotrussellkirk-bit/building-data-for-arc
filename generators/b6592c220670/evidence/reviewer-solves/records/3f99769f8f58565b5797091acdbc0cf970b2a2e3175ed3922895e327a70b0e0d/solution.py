"""Independent visible-example solution; standard library only."""


def solve(grid):
    if not grid or len(grid) < 3 or not grid[0] or any(len(r) != len(grid[0]) for r in grid):
        raise ValueError('expected a rectangular scene with script and body')
    points = [(r, c) for r in range(2, len(grid)) for c, value in enumerate(grid[r]) if value]
    if not points:
        raise ValueError('missing motif')
    r0, r1 = min(r for r, _ in points), max(r for r, _ in points)
    c0, c1 = min(c for _, c in points), max(c for _, c in points)
    state = [list(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]]
    panels = []
    for code in grid[0]:
        if code == 0:
            continue
        if code == 2:
            state = [[state[len(state) - 1 - r][c] for r in range(len(state))]
                     for c in range(len(state[0]))]
        elif code == 3:
            state = [list(reversed(row)) for row in state]
        elif code == 4:
            state = [list(reversed(row)) for row in reversed(state)]
        elif code != 1:
            raise ValueError('unknown instruction')
        panels.append([row[:] for row in state])
    if not panels:
        return [[0]]
    out = [[0] * (sum(len(p[0]) for p in panels) + len(panels) - 1)
           for _ in range(max(map(len, panels)))]
    left = 0
    for panel in panels:
        for r, row in enumerate(panel):
            out[r][left:left + len(row)] = row
        left += len(panel[0]) + 1
    return out
