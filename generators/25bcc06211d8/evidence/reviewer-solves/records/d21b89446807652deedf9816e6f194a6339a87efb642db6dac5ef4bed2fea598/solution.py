"""Visible-example-only solution for blind task 25bcc06211d8."""

from __future__ import annotations

from collections import deque
from typing import List, Sequence, Tuple

Grid = List[List[int]]
Coord = Tuple[int, int]


def _components(grid: Sequence[Sequence[int]]) -> list[tuple[int, list[Coord]]]:
    """Return 4-connected monochromatic non-background components."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen: set[Coord] = set()
    out: list[tuple[int, list[Coord]]] = []

    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            q: deque[Coord] = deque([(r, c)])
            seen.add((r, c))
            cells: list[Coord] = []
            while q:
                rr, cc = q.popleft()
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
                        q.append((nr, nc))
            out.append((color, cells))
    return out


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    """Compact each bent component into its centered cross/T/L form."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    result: Grid = [[0 for _ in range(w)] for _ in range(h)]

    for color, cells in _components(grid):
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)
        bh, bw = r1 - r0 + 1, c1 - c0 + 1
        target: set[Coord]

        if len(cells) == 5 and bh == 3 and bw == 3:
            # Two end protrusions of a length-three spine move to its midpoint.
            target = {
                (r0 + 1, c0 + 1),
                (r0, c0 + 1),
                (r0 + 2, c0 + 1),
                (r0 + 1, c0),
                (r0 + 1, c0 + 2),
            }
        elif len(cells) == 4 and bh == 2 and bw == 3:
            # Preserve which row is the three-cell spine and center the branch.
            row_counts = {
                r: sum(1 for rr, _ in cells if rr == r) for r in (r0, r1)
            }
            spine_r = max(row_counts, key=row_counts.get)
            branch_r = r1 if spine_r == r0 else r0
            target = {(spine_r, c) for c in range(c0, c1 + 1)}
            target.add((branch_r, c0 + 1))
        elif len(cells) == 4 and bh == 3 and bw == 2:
            # Preserve which column is the three-cell spine and center the branch.
            col_counts = {
                c: sum(1 for _, cc in cells if cc == c) for c in (c0, c1)
            }
            spine_c = max(col_counts, key=col_counts.get)
            branch_c = c1 if spine_c == c0 else c0
            target = {(r, spine_c) for r in range(r0, r1 + 1)}
            target.add((r0 + 1, branch_c))
        elif len(cells) == 3 and bh == 2 and bw == 2:
            # The sole visible triomino is normalized to the upper-left L.
            target = {(r0, c0), (r0, c1), (r1, c0)}
        else:
            # Conservative fallback for any structure not evidenced by examples.
            target = set(cells)

        for r, c in target:
            result[r][c] = color

    return result
