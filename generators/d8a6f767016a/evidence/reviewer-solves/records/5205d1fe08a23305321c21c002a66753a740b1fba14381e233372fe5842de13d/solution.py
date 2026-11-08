"""ARC solution inferred from the visible demonstrations only.

Each 4-connected non-background object is recolored according to the number of
background regions it encloses.  Objects with no enclosed region are unchanged.
"""

from collections import deque
from typing import Iterable, List, Sequence, Set, Tuple

Grid = List[List[int]]
Cell = Tuple[int, int]

_NEIGHBORS: Tuple[Cell, ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))
_COLOR_BY_HOLE_COUNT = {1: 1, 2: 3, 3: 2, 4: 4}


def _neighbors(r: int, c: int, h: int, w: int) -> Iterable[Cell]:
    for dr, dc in _NEIGHBORS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            yield nr, nc


def _components(grid: Sequence[Sequence[int]], background: int = 0) -> List[Set[Cell]]:
    """Return 4-connected non-background components."""

    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != background}
    result: List[Set[Cell]] = []

    while unseen:
        start = next(iter(unseen))
        value = grid[start[0]][start[1]]
        component = {start}
        unseen.remove(start)
        queue = deque([start])

        while queue:
            r, c = queue.popleft()
            for nr, nc in _neighbors(r, c, h, w):
                nxt = (nr, nc)
                if nxt in unseen and grid[nr][nc] == value:
                    unseen.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)

        result.append(component)

    return result


def _hole_count(component: Set[Cell]) -> int:
    """Count bounded 4-connected background regions enclosed by one component.

    The component is embedded in a one-cell padded local canvas.  Flooding open
    cells from that canvas boundary marks the exterior; every remaining open
    component is a hole.  Cells belonging to other source objects are omitted
    from the local mask, so the count is a property of this component alone.
    """

    min_r = min(r for r, _ in component)
    max_r = max(r for r, _ in component)
    min_c = min(c for _, c in component)
    max_c = max(c for _, c in component)

    # Local coordinates have a one-cell exterior border around the bounding box.
    local_h = (max_r - min_r + 1) + 2
    local_w = (max_c - min_c + 1) + 2
    walls = {(r - min_r + 1, c - min_c + 1) for r, c in component}
    open_cells = {
        (r, c)
        for r in range(local_h)
        for c in range(local_w)
        if (r, c) not in walls
    }

    exterior: Set[Cell] = set()
    queue: deque[Cell] = deque()
    for r, c in open_cells:
        if r in (0, local_h - 1) or c in (0, local_w - 1):
            exterior.add((r, c))
            queue.append((r, c))

    while queue:
        r, c = queue.popleft()
        for nr, nc in _neighbors(r, c, local_h, local_w):
            nxt = (nr, nc)
            if nxt in open_cells and nxt not in exterior:
                exterior.add(nxt)
                queue.append(nxt)

    enclosed = open_cells - exterior
    holes = 0
    while enclosed:
        holes += 1
        start = next(iter(enclosed))
        enclosed.remove(start)
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for nr, nc in _neighbors(r, c, local_h, local_w):
                nxt = (nr, nc)
                if nxt in enclosed:
                    enclosed.remove(nxt)
                    queue.append(nxt)

    return holes


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    """Recolor each nonzero object by its number of enclosed regions."""

    if not grid or not grid[0]:
        return [list(row) for row in grid]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    output = [list(row) for row in grid]
    for component in _components(grid):
        holes = _hole_count(component)
        color = _COLOR_BY_HOLE_COUNT.get(holes)
        if color is None:
            continue
        for r, c in component:
            output[r][c] = color
    return output
