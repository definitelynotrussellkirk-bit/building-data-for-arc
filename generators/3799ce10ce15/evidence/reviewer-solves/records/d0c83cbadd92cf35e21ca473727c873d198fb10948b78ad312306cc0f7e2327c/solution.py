from collections import deque


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    out = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        todo = deque([start])
        cells = {start}
        while todo:
            r, c = todo.popleft()
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (rr, cc) in unseen:
                    unseen.remove((rr, cc))
                    cells.add((rr, cc))
                    todo.append((rr, cc))
        out.append(cells)
    return out


def _frames(grid):
    frames = []
    for cells in _components(grid, 9):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(cols), max(cols)
        if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
            continue
        border = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if cells == border:
            frames.append((r0, c0, r1, c1))
    return sorted(frames)


def solve(grid):
    legend = [value for value in grid[0] if value not in (0, 9)]
    output = []
    for r0, c0, r1, c1 in _frames(grid):
        present = {
            grid[r][c]
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
            if grid[r][c] not in (0, 9)
        }
        output.append([color if color in present else 0 for color in legend])
    return output
