"""Visible-example-only ARC solver for blind episode 93ca517eac25."""

from collections import deque


def _components(grid, predicate):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or not predicate(grid[r][c]):
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while q:
                x, y = q.popleft()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < h
                        and 0 <= ny < w
                        and (nx, ny) not in seen
                        and predicate(grid[nx][ny])
                    ):
                        seen.add((nx, ny))
                        q.append((nx, ny))
            out.append(cells)
    return out


def _shape(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _holes(cells):
    """4-connected background components inside the component's tight box."""
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    h, w = r1 - r0 + 1, c1 - c0 + 1
    occupied = {(r - r0, c - c0) for r, c in cells}
    missing = {(r, c) for r in range(h) for c in range(w)} - occupied
    seen = set()
    holes = []
    for start in sorted(missing):
        if start in seen:
            continue
        q = [start]
        seen.add(start)
        part = []
        while q:
            r, c = q.pop()
            part.append((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = (r + dr, c + dc)
                if p in missing and p not in seen:
                    seen.add(p)
                    q.append(p)
        holes.append(part)
    return holes, h, w


def _distance(a, b):
    return min(abs(r - x) + abs(c - y) for r, c in a for x, y in b)


def solve(grid):
    out = [row[:] for row in grid]
    blue = _components(grid, lambda v: v == 1)

    # The examples use the non-blue colors as oriented shape keys.  Preserve
    # orientation: a vertical domino distinguishes the vertical-gap object
    # from the otherwise analogous horizontal-gap object.
    clues = []
    for cells in _components(grid, lambda v: v not in (0, 1, 2)):
        color = grid[cells[0][0]][cells[0][1]]
        clues.append((color, cells, _shape(cells)))
    clues.sort(key=lambda item: item[0])

    chosen = None
    for _color, clue_cells, clue_shape in clues:
        candidates = []
        for cells in blue:
            holes, h, w = _holes(cells)
            if not holes or any(_shape(part) != clue_shape for part in holes):
                continue
            internal = sum(
                0 < r < h - 1 and 0 < c < w - 1
                for part in holes
                for r, c in part
            )
            # Prefer the strongest repeated match, then a boundary-carved
            # silhouette, then the object spatially associated with the key.
            score = (-len(holes), internal, _distance(cells, clue_cells), -len(cells))
            candidates.append((score, cells))
        if candidates:
            candidates.sort(key=lambda item: item[0])
            chosen = candidates[0][1]
            break

    if chosen is None:
        # Conservative fallback for an unseen key: choose the blue component
        # with the richest tight-box negative space rather than altering all.
        chosen = max(blue, key=lambda cells: (len(_holes(cells)[0]), len(cells)))

    for r, c in chosen:
        out[r][c] = 2
    return out
