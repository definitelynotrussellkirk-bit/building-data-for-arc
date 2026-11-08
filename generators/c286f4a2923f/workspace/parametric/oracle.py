"""Independent Python semantics for the c286f4a2923f parametric family."""
from __future__ import annotations

from collections import deque
from copy import deepcopy


def _cells(grid: list[list[int]], color: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    if not cells:
        raise ValueError("missing colored object")
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def transfer_only(grid: list[list[int]]) -> list[list[int]]:
    if not grid or not grid[0]:
        raise ValueError("grid must be nonempty")
    source = _cells(grid, 2)
    target = _cells(grid, 3)
    sr0, sc0, _, _ = _bbox(source)
    tr0, tc0, tr1, tc1 = _bbox(target)
    expected_target = {
        (r, c)
        for r in range(tr0, tr1 + 1)
        for c in range(tc0, tc1 + 1)
    }
    if set(target) != expected_target:
        raise ValueError("color-3 target must be a solid rectangle")
    out = [[0 for _ in row] for row in grid]
    for r, c in source:
        rr, cc = tr0 + (r - sr0), tc0 + (c - sc0)
        if not (0 <= rr < len(grid) and 0 <= cc < len(grid[0])):
            raise ValueError("source mask does not fit target anchor")
        out[rr][cc] = 8
    return out


def zero_regions(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 0}
    regions: list[list[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        region = [start]
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    queue.append(nxt)
                    region.append(nxt)
        regions.append(sorted(region))
    return regions


def enclosed_regions(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    return [
        region
        for region in zero_regions(grid)
        if all(r not in (0, height - 1) and c not in (0, width - 1) for r, c in region)
    ]


def fill_transferred_holes(grid: list[list[int]]) -> list[list[int]]:
    out = transfer_only(grid)
    for region in enclosed_regions(out):
        for r, c in region:
            out[r][c] = 4
    return out


def solve(grid: list[list[int]], finish: str) -> list[list[int]]:
    if finish == "transfer_only":
        return transfer_only(grid)
    if finish == "fill_transferred_holes":
        return fill_transferred_holes(grid)
    raise ValueError(f"unknown finish: {finish}")


def describe(grid: list[list[int]], finish: str) -> dict[str, object]:
    source = _cells(grid, 2)
    target = _cells(grid, 3)
    sr0, sc0, sr1, sc1 = _bbox(source)
    tr0, tc0, tr1, tc1 = _bbox(target)
    transferred = transfer_only(grid)
    regions = enclosed_regions(transferred)
    return {
        "finish": finish,
        "shape": [len(grid), len(grid[0])],
        "source_cells": len(source),
        "source_bbox": [sr0, sc0, sr1, sc1],
        "target_bbox": [tr0, tc0, tr1, tc1],
        "enclosed_regions": len(regions),
        "enclosed_cells": sum(map(len, regions)),
    }
