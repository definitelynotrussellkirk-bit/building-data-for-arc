"""Visible-example solution for the reviewer-authored ARC episode."""
from __future__ import annotations


def _support(panel: list[list[int]]) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value != 0
    }


def _normalize(points: set[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    if not points:
        return frozenset()
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return frozenset((r - r0, c - c0) for r, c in points)


def _d4_signature(points: set[tuple[int, int]]) -> frozenset[frozenset[tuple[int, int]]]:
    """All normalized rotations/reflections of a finite cell set."""
    transforms = (
        lambda r, c: (r, c),
        lambda r, c: (r, -c),
        lambda r, c: (-r, c),
        lambda r, c: (-r, -c),
        lambda r, c: (c, r),
        lambda r, c: (c, -r),
        lambda r, c: (-c, r),
        lambda r, c: (-c, -r),
    )
    return frozenset(
        _normalize({transform(r, c) for r, c in points})
        for transform in transforms
    )


def _crop_recolor(panel: list[list[int]], color: int) -> list[list[int]]:
    points = _support(panel)
    if not points:
        return []
    r0 = min(r for r, _ in points)
    r1 = max(r for r, _ in points)
    c0 = min(c for _, c in points)
    c1 = max(c for _, c in points)
    return [
        [color if panel[r][c] != 0 else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Select the prototype matching the query up to D4 symmetry.

    The input has three equal-width panels separated by two columns.  The first
    two panels are prototypes; the third is a query.  Return the displayed
    orientation of the matching prototype, tightly cropped and recolored with
    the query's color.
    """
    if not grid or not grid[0]:
        return []
    width = len(grid[0])
    if any(len(row) != width for row in grid) or (width - 2) % 3:
        raise ValueError("expected three equal panels separated by two columns")

    panel_width = (width - 2) // 3
    starts = (0, panel_width + 1, 2 * panel_width + 2)
    panels = [
        [row[start : start + panel_width] for row in grid]
        for start in starts
    ]
    query = panels[2]
    query_points = _support(query)
    if not query_points:
        raise ValueError("query panel is empty")
    query_colors = {
        value for row in query for value in row if value != 0
    }
    if len(query_colors) != 1:
        raise ValueError("query panel must use one foreground color")
    query_color = next(iter(query_colors))
    query_signature = _d4_signature(query_points)

    matches = [
        prototype
        for prototype in panels[:2]
        if _normalize(_support(prototype)) in query_signature
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one matching prototype, found {len(matches)}")
    return _crop_recolor(matches[0], query_color)
