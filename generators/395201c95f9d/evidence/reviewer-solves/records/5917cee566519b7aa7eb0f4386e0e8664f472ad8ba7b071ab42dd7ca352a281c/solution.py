from __future__ import annotations


def _normalize(cells):
    cells = list(cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _dims(cells):
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _variants(cells):
    cells = _normalize(cells)
    h, w = _dims(cells)
    raw = [
        cells,
        [(c, h - 1 - r) for r, c in cells],
        [(h - 1 - r, w - 1 - c) for r, c in cells],
        [(w - 1 - c, r) for r, c in cells],
        [(r, w - 1 - c) for r, c in cells],
        [(h - 1 - r, c) for r, c in cells],
        [(c, r) for r, c in cells],
        [(w - 1 - c, h - 1 - r) for r, c in cells],
    ]
    return {_normalize(shape) for shape in raw}


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    separators = [
        c for c in range(width) if all(grid[r][c] == 9 for r in range(height))
    ]
    if len(separators) != 2:
        raise ValueError("expected two full-height separator columns")
    s0, s1 = separators
    panel_width = s0
    lefts = (0, s0 + 1, s1 + 1)

    labels = (grid[0][lefts[0]], grid[0][lefts[1]])
    prototypes = []
    for left in lefts[:2]:
        cells = []
        for r in range(height):
            for c in range(panel_width):
                if (r, c) == (0, 0):
                    continue
                if grid[r][left + c] != 0:
                    cells.append((r, c))
        prototypes.append(_normalize(cells))

    query_cells = []
    for r in range(height):
        for c in range(panel_width):
            if grid[r][lefts[2] + c] != 0:
                query_cells.append((r, c))
    query_shape = _normalize(query_cells)

    matches = [i for i, shape in enumerate(prototypes) if query_shape in _variants(shape)]
    if len(matches) != 1:
        raise ValueError(f"expected one matching prototype, found {len(matches)}")

    output = [[0] * panel_width for _ in range(height)]
    color = labels[matches[0]]
    for r, c in query_cells:
        output[r][c] = color
    return output
