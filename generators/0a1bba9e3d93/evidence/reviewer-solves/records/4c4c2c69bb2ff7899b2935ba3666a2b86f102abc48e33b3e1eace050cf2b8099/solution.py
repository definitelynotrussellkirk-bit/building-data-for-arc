"""Visible-example solution for task 0a1bba9e3d93.

The input is three equal-width panels separated by full color-8 columns.
The first two panels describe a shape growth mask; the third is the query.
"""
from __future__ import annotations


def _split_panels(grid: list[list[int]]) -> list[list[list[int]]]:
    """Split on columns that are entirely color 8."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    separators = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    cuts = [-1, *separators, w]
    panels = []
    for left, right in zip(cuts, cuts[1:]):
        if right > left + 1:
            panels.append([row[left + 1 : right] for row in grid])
    return panels


def _support(panel: list[list[int]]) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value != 0
    }


def _normalize(cells: set[tuple[int, int]]) -> tuple[set[tuple[int, int]], tuple[int, int]]:
    if not cells:
        return set(), (0, 0)
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return {(r - top, c - left) for r, c in cells}, (top, left)


def _growth_mask(
    before: set[tuple[int, int]],
    after: set[tuple[int, int]],
    query: set[tuple[int, int]],
    query_anchor: tuple[int, int],
    height: int,
    width: int,
) -> set[tuple[int, int]]:
    """Infer cells added from BEFORE to AFTER.

    Shape placement is irrelevant, so supports are normalized first.  When
    multiple translations of BEFORE overlap AFTER equally well, prefer the one
    whose added cells make the most observable (new, in-bounds) changes to the
    query.  This resolves the ambiguous large demonstration without consulting
    hidden labels.
    """
    if not after:
        return set()

    max_r = max([r for r, _ in before | after] or [0])
    max_c = max([c for _, c in before | after] or [0])
    radius_r = max_r + 2
    radius_c = max_c + 2
    qr0, qc0 = query_anchor

    best_score = None
    best_delta: set[tuple[int, int]] = set(after)
    for dr in range(-radius_r, radius_r + 1):
        for dc in range(-radius_c, radius_c + 1):
            shifted = {(r + dr, c + dc) for r, c in before}
            overlap = len(shifted & after)
            delta = after - shifted
            observable_new = 0
            for r, c in delta:
                rr, cc = qr0 + r, qc0 + c
                if 0 <= rr < height and 0 <= cc < width and (r, c) not in query:
                    observable_new += 1
            score = (
                overlap,
                observable_new,
                -abs(dr) - abs(dc),
                -abs(dr),
                -abs(dc),
                -dr,
                -dc,
            )
            if best_score is None or score > best_score:
                best_score = score
                best_delta = delta
    return best_delta


def solve(grid: list[list[int]]) -> list[list[int]]:
    panels = _split_panels(grid)
    if len(panels) != 3:
        raise ValueError(f"expected three panels, found {len(panels)}")

    before_panel, after_panel, query_panel = panels
    height = len(query_panel)
    width = len(query_panel[0]) if height else 0

    before, _ = _normalize(_support(before_panel))
    after, _ = _normalize(_support(after_panel))
    query_abs = _support(query_panel)
    query, query_anchor = _normalize(query_abs)

    colors = [value for row in query_panel for value in row if value != 0]
    if not colors:
        return [[0] * width for _ in range(height)]
    color = colors[0]

    additions = _growth_mask(
        before,
        after,
        query,
        query_anchor,
        height,
        width,
    )

    out = [[0] * width for _ in range(height)]
    for r, c in query_abs:
        out[r][c] = query_panel[r][c]
    top, left = query_anchor
    for dr, dc in additions:
        r, c = top + dr, left + dc
        if 0 <= r < height and 0 <= c < width:
            out[r][c] = color
    return out
