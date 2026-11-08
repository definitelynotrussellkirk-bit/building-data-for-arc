"""Visible-example solution for the prepared 2f0f072d3d7e episode."""


def _normalize(cells):
    cells = tuple(cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rotate_cw(cells):
    cells = _normalize(cells)
    if not cells:
        return ()
    height = max(r for r, _ in cells) + 1
    return _normalize((c, height - 1 - r) for r, c in cells)


def _reflect_lr(cells):
    cells = _normalize(cells)
    if not cells:
        return ()
    width = max(c for _, c in cells) + 1
    return _normalize((r, width - 1 - c) for r, c in cells)


def _transform(cells, code):
    cells = _normalize(cells)
    if code == 4:
        return _reflect_lr(cells)
    for _ in range(code):
        cells = _rotate_cw(cells)
    return cells


def _split_panels(grid):
    height = len(grid)
    width = len(grid[0])
    cuts = [c for c in range(width) if all(grid[r][c] == 9 for r in range(height))]
    bounds = [-1] + cuts + [width]
    return [[row[left + 1:right] for row in grid] for left, right in zip(bounds, bounds[1:])]


def _support(panel):
    return tuple(
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value not in (0, 9)
    )


def solve(grid):
    panels = _split_panels(grid)
    supports = [_support(panel) for panel in panels]

    normalized_b = _normalize(supports[1])
    code = 0
    for candidate_code in range(4):
        if _transform(supports[0], candidate_code) == normalized_b:
            code = candidate_code
            break
    else:
        if _reflect_lr(supports[0]) == normalized_b:
            code = 4

    target = _transform(supports[2], code)
    winner = None
    for candidate in supports[3:]:
        if _normalize(candidate) == target:
            winner = candidate
            break

    side = len(panels[0])
    occupied = set(winner or ())
    return [
        [8 if (r, c) in occupied else 0 for c in range(side)]
        for r in range(side)
    ]
