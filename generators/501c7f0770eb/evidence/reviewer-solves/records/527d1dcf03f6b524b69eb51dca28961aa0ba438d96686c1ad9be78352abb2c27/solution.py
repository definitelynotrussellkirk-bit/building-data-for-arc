from __future__ import annotations


def _gray_components(grid):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    }
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def _rectangular_frame(component):
    rows = [r for r, _ in component]
    cols = [c for _, c in component]
    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)
    border = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    if component == border and r1 - r0 >= 2 and c1 - c0 >= 2:
        return r0, r1, c0, c1
    return None


def solve(grid):
    source = [list(row) for row in grid]
    output = [row[:] for row in source]

    for component in _gray_components(source):
        frame = _rectangular_frame(component)
        if frame is None:
            # Touching frames form one non-rectangular gray component and,
            # as shown by training example 1, remain inactive.
            continue
        r0, r1, c0, c1 = frame
        seeds = [
            (r, c, source[r][c])
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
            if source[r][c] in (1, 2)
        ]
        for sr, sc, color in seeds:
            directions = ((-1, 0), (1, 0)) if color == 1 else ((0, -1), (0, 1))
            output[sr][sc] = 7
            for dr, dc in directions:
                r, c = sr + dr, sc + dc
                while r0 < r < r1 and c0 < c < c1:
                    if source[r][c] == 4:
                        break
                    output[r][c] = 7
                    r += dr
                    c += dc

    return output
