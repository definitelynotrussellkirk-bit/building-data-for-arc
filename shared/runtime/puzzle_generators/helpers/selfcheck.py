"""Small invariant helpers for generator self_check() functions.

These helpers intentionally avoid importing the generator runtime so they can be
used by lightweight per-generator executable invariants.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Callable, Iterable

Grid = list[list[int]]
Cell = tuple[int, int]


def color_counts(grid):
    return Counter(v for row in grid for v in row)


def nonzero_cells(grid, *, exclude: set[int] | None = None):
    ex = exclude or set()
    return [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row)
            if v != 0 and v not in ex]


def bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = list(cells)
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def norm(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = list(cells)
    r1, c1, _, _ = bbox(cells)
    return tuple(sorted((r - r1, c - c1) for r, c in cells))


def components(grid, *, colors: set[int] | None = None, same_color: bool = True,
               connectivity: int = 4):
    h, w = len(grid), len(grid[0])
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if connectivity == 8:
        dirs = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                if dr or dc]
    seen: set[tuple[int, int]] = set()
    out = []
    for r in range(h):
        for c in range(w):
            col = grid[r][c]
            if (r, c) in seen or col == 0 or (colors is not None and col not in colors):
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in dirs:
                    nr, nc = rr + dr, cc + dc
                    if not (0 <= nr < h and 0 <= nc < w) or (nr, nc) in seen:
                        continue
                    ncol = grid[nr][nc]
                    if ncol == 0 or (colors is not None and ncol not in colors):
                        continue
                    if same_color and ncol != col:
                        continue
                    seen.add((nr, nc))
                    q.append((nr, nc))
            b = bbox(cells)
            out.append({"color": col, "cells": cells, "bbox": b, "norm": norm(cells)})
    return out


def has_row_gap(cells: Iterable[tuple[int, int]]) -> bool:
    by_row: dict[int, list[int]] = {}
    cellset = set(cells)
    for r, c in cellset:
        by_row.setdefault(r, []).append(c)
    for r, cols in by_row.items():
        if len(cols) < 2:
            continue
        lo, hi = min(cols), max(cols)
        if any((r, c) not in cellset for c in range(lo + 1, hi)):
            return True
    return False


def components_have_clearance(grid, comps, *, diagonal: bool = True) -> bool:
    """True if distinct components have at least a one-cell 0 moat."""
    owner = {}
    for i, comp in enumerate(comps):
        for cell in comp["cells"]:
            owner[cell] = i
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diagonal:
        dirs = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                if dr or dc]
    h, w = len(grid), len(grid[0])
    for (r, c), i in owner.items():
        for dr, dc in dirs:
            nb = (r + dr, c + dc)
            if 0 <= nb[0] < h and 0 <= nb[1] < w and nb in owner and owner[nb] != i:
                return False
    return True


def is_full_frame_component(comp, *, color: int, min_size: int = 4) -> bool:
    if comp["color"] != color:
        return False
    r1, c1, r2, c2 = comp["bbox"]
    if r2 - r1 + 1 < min_size or c2 - c1 + 1 < min_size:
        return False
    want = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
            if r in (r1, r2) or c in (c1, c2)}
    return set(comp["cells"]) == want


def interior_cells(b: tuple[int, int, int, int]):
    r1, c1, r2, c2 = b
    return [(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)]


# --- Geometry helpers from reviewer bundle 174 -----------------------------
# Merged in 2026-06-28. NOTE: bundle 174 also shipped a `components()` that
# returns plain lists of cells (vs the dict-returning `components()` above that
# bundle-170 generators rely on). To avoid a name collision the list-returning
# variant is exposed here as `components_cells`; the four 174 generators that
# imported it use `import components_cells as components`.


def dims(g: Grid) -> tuple[int, int]:
    return len(g), len(g[0]) if g else 0


def positions(g: Grid, *, colors: Iterable[int] | None = None,
              pred: Callable[[int], bool] | None = None) -> list[Cell]:
    color_set = set(colors) if colors is not None else None
    out: list[Cell] = []
    for r, row in enumerate(g):
        for c, v in enumerate(row):
            if color_set is not None:
                ok = v in color_set
            elif pred is not None:
                ok = pred(v)
            else:
                ok = v != 0
            if ok:
                out.append((r, c))
    return out


def normalize(cells: Iterable[Cell]) -> tuple[Cell, ...]:
    cells = list(cells)
    if not cells:
        return ()
    r1, c1, _r2, _c2 = bbox(cells)
    return tuple(sorted((r - r1, c - c1) for r, c in cells))


def d4_transform(cells: Iterable[Cell], code: int) -> tuple[Cell, ...]:
    raw: list[Cell] = []
    for r, c in cells:
        if code == 1:
            raw.append((c, -r))
        elif code == 2:
            raw.append((-r, -c))
        elif code == 3:
            raw.append((-c, r))
        elif code == 4:
            raw.append((r, -c))
        elif code == 5:
            raw.append((-r, c))
        elif code == 6:
            raw.append((c, r))
        elif code == 7:
            raw.append((-c, -r))
        else:
            raw.append((r, c))
    return normalize(raw)


def transpose_cells(cells: Iterable[Cell]) -> tuple[Cell, ...]:
    return d4_transform(cells, 6)


def components_cells(g: Grid, *, colors: Iterable[int] | None = None,
                     same_color: bool = False, nonzero: bool = True) -> list[list[Cell]]:
    """4-connected components as plain cell lists (bundle-174 variant).

    If same_color=True, neighbours must match the start cell's colour. Otherwise
    all selected colours/nonzero cells are considered mutually connected.
    """
    h, w = dims(g)
    color_set = set(colors) if colors is not None else None
    seen: set[Cell] = set()
    out: list[list[Cell]] = []

    def selectable(v: int, start: int | None = None) -> bool:
        if color_set is not None and v not in color_set:
            return False
        if color_set is None and nonzero and v == 0:
            return False
        if same_color and start is not None and v != start:
            return False
        return True

    for r in range(h):
        for c in range(w):
            if (r, c) in seen or not selectable(g[r][c]):
                continue
            start = g[r][c]
            q: deque[Cell] = deque([(r, c)])
            seen.add((r, c))
            comp: list[Cell] = []
            while q:
                rr, cc = q.popleft()
                comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen:
                        if selectable(g[nr][nc], start):
                            seen.add((nr, nc))
                            q.append((nr, nc))
            out.append(comp)
    return out


def rect_border_cells(r1: int, c1: int, r2: int, c2: int) -> set[Cell]:
    return {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
            if r in (r1, r2) or c in (c1, c2)}


def color_rect_frames(g: Grid, color: int = 8,
                      *, min_outer_h: int = 3, min_outer_w: int = 3) -> list[tuple[int, int, int, int]]:
    """Return bboxes of connected `color` components that are exact hollow rectangles."""
    frames: list[tuple[int, int, int, int]] = []
    for comp in components_cells(g, colors={color}):
        r1, c1, r2, c2 = bbox(comp)
        if r2 - r1 + 1 < min_outer_h or c2 - c1 + 1 < min_outer_w:
            continue
        if set(comp) == rect_border_cells(r1, c1, r2, c2):
            frames.append((r1, c1, r2, c2))
    return sorted(frames)
