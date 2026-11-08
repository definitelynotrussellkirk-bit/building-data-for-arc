"""Visible-example solution: match the query silhouette under square symmetries."""


def _normalize(points):
    if not points:
        return frozenset()
    r0 = min(r for r, c in points)
    c0 = min(c for r, c in points)
    return frozenset((r - r0, c - c0) for r, c in points)


def _variants(points):
    variants = set()
    for swap in (False, True):
        for sr in (-1, 1):
            for sc in (-1, 1):
                transformed = [(sr * (c if swap else r), sc * (r if swap else c))
                               for r, c in points]
                variants.add(_normalize(transformed))
    return variants


def solve(grid):
    h, w = len(grid), len(grid[0])
    separators = [c for c in range(w)
                  if grid[0][c] != 0 and all(grid[r][c] == grid[0][c] for r in range(h))]
    if len(separators) != 2:
        raise ValueError("Expected three panels separated by two solid columns")
    a, b = separators
    panels = [[row[:a] for row in grid],
              [row[a + 1:b] for row in grid],
              [row[b + 1:] for row in grid]]
    query = panels[2]
    target = {(r, c) for r, row in enumerate(query) for c, v in enumerate(row) if v != 0}
    normalized = _normalize(target)
    matches = []
    for panel in panels[:2]:
        marker = panel[0][0]
        shape = {(r, c) for r, row in enumerate(panel) for c, v in enumerate(row)
                 if v != 0 and (r, c) != (0, 0)}
        if normalized in _variants(shape):
            matches.append(marker)
    if len(matches) != 1:
        raise ValueError(f"Expected one matching labelled silhouette, got {len(matches)}")
    color = matches[0]
    return [[color if v != 0 else 0 for v in row] for row in query]
