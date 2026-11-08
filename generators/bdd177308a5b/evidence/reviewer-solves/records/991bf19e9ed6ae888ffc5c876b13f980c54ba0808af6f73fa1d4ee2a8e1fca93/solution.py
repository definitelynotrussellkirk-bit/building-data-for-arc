from __future__ import annotations


def _components(grid, excluded):
    h, w = len(grid), len(grid[0])
    seen = set()
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color in excluded or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            yield color, cells


def _normalized(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def solve(grid):
    """Recolor the external object matching the framed template exactly."""
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]

    # The 5-cells form an L: choose its fullest row and column.  Their
    # intersection is the lower-right corner of the template compartment.
    five_by_row = [sum(value == 5 for value in row) for row in grid]
    five_by_col = [sum(grid[r][c] == 5 for r in range(h)) for c in range(w)]
    frame_row = max(range(h), key=five_by_row.__getitem__)
    frame_col = max(range(w), key=five_by_col.__getitem__)

    template_cells = [
        (r, c)
        for r in range(frame_row)
        for c in range(frame_col)
        if grid[r][c] not in (0, 5)
    ]
    if not template_cells:
        return out
    template_shape = _normalized(template_cells)
    template_set = set(template_cells)

    for _, cells in _components(grid, excluded={0, 5}):
        if template_set.intersection(cells):
            continue
        if _normalized(cells) == template_shape:
            for r, c in cells:
                out[r][c] = 5
    return out
