from copy import deepcopy


def _one_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = set()
            while stack:
                cr, cc = stack.pop()
                cells.add((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return components


def _rectangular_frame(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)
    perimeter = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    return (r0, c0, r1, c1) if cells == perimeter else None


def solve(grid):
    """Fill the interior of the innermost rectangular frame around each 2."""
    out = deepcopy(grid)
    frames = []
    for component in _one_components(grid):
        frame = _rectangular_frame(component)
        if frame is not None:
            frames.append(frame)

    chosen = set()
    for sr, row in enumerate(grid):
        for sc, value in enumerate(row):
            if value != 2:
                continue
            containing = [
                frame
                for frame in frames
                if frame[0] < sr < frame[2] and frame[1] < sc < frame[3]
            ]
            if containing:
                chosen.add(
                    min(
                        containing,
                        key=lambda f: ((f[2] - f[0] + 1) * (f[3] - f[1] + 1), f),
                    )
                )

    for r0, c0, r1, c1 in chosen:
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                out[r][c] = 3
    return out
