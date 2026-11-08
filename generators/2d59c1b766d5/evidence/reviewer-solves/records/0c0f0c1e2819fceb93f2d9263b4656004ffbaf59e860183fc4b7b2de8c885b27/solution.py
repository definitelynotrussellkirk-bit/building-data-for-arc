from collections import deque

DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(cells):
    remaining = set(cells)
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = [start]
        comp = {start}
        for r, c in queue:
            for dr, dc in DIR4:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    comp.add(nxt)
                    queue.append(nxt)
        result.append(comp)
    return result


def solve(grid):
    out = [row[:] for row in grid]
    frame_cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    }
    for component in _components(frame_cells):
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        gates = [
            (r, c)
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
            if grid[r][c] not in (0, 5, 8)
        ]
        if not gates:
            continue
        gate = gates[0]
        color = grid[gate[0]][gate[1]]
        seen = {gate}
        queue = deque([gate])
        while queue:
            r, c = queue.popleft()
            for dr, dc in DIR4:
                nr, nc = r + dr, c + dc
                if not (r0 < nr < r1 and c0 < nc < c1):
                    continue
                if (nr, nc) in seen or grid[nr][nc] not in (0, color):
                    continue
                seen.add((nr, nc))
                queue.append((nr, nc))
        for r, c in seen:
            out[r][c] = color
    return out
