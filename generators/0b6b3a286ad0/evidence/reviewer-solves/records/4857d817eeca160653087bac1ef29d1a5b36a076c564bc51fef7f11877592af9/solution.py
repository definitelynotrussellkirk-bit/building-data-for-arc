"""Visible-example solution for ARC task 0b6b3a286ad0."""
from __future__ import annotations


def _split_panels(grid: list[list[int]]) -> list[list[list[int]]]:
    """Split on full-height color-9 separator columns."""
    height = len(grid)
    width = len(grid[0])
    separators = [
        c for c in range(width)
        if all(grid[r][c] == 9 for r in range(height))
    ]
    bounds = [-1, *separators, width]
    return [
        [row[bounds[i] + 1:bounds[i + 1]] for row in grid]
        for i in range(len(bounds) - 1)
    ]


def _crop_nonzero(panel: list[list[int]]) -> list[list[int]]:
    cells = [
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return []
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0:c1 + 1] for row in panel[r0:r1 + 1]]


def _contains_masked(query: list[list[int]], key: list[list[int]]) -> bool:
    """Find key in query, treating zero cells in the key as wildcards."""
    if not key:
        return False
    qh, qw = len(query), len(query[0])
    kh, kw = len(key), len(key[0])
    for r0 in range(qh - kh + 1):
        for c0 in range(qw - kw + 1):
            if all(
                key[r][c] == 0 or query[r0 + r][c0 + c] == key[r][c]
                for r in range(kh)
                for c in range(kw)
            ):
                return True
    return False


def solve(grid: list[list[int]]) -> list[list[int]]:
    panels = _split_panels(grid)
    if len(panels) != 5:
        raise ValueError(f"expected five panels, found {len(panels)}")

    key_1 = _crop_nonzero(panels[0])
    value_1 = _crop_nonzero(panels[1])
    key_2 = _crop_nonzero(panels[2])
    value_2 = _crop_nonzero(panels[3])
    query = panels[4]

    match_1 = _contains_masked(query, key_1)
    match_2 = _contains_masked(query, key_2)
    if match_1 and not match_2:
        return value_1
    if match_2 and not match_1:
        return value_2
    if match_1:
        # The visible curriculum always identifies one key. This deterministic
        # fallback keeps execution defined if a future query contains both.
        return value_1
    raise ValueError("query contains neither visible key")
