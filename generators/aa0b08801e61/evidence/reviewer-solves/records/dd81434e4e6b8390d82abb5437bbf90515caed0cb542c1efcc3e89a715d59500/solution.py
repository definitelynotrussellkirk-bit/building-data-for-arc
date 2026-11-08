"""Visible-example solution for the blind ARC task.

Each non-background object is recolored by the orientation of its geometric
symmetry.  The target colors distinguish cell-centred vertical (2),
horizontal (3), diagonal/half-turn (4), and odd-by-odd four-way (8)
symmetry.  Components are handled independently.
"""

from collections import deque


def _normalize(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return frozenset((r - min_r, c - min_c) for r, c in cells)


def _transform(cells, kind):
    """Return a normalized transformed copy of a normalized cell set."""
    if kind == "horizontal":
        transformed = [(-r, c) for r, c in cells]
    elif kind == "vertical":
        transformed = [(r, -c) for r, c in cells]
    elif kind == "half_turn":
        transformed = [(-r, -c) for r, c in cells]
    elif kind == "main_diagonal":
        transformed = [(c, r) for r, c in cells]
    elif kind == "anti_diagonal":
        transformed = [(-c, -r) for r, c in cells]
    else:  # pragma: no cover - internal programming error
        raise ValueError(kind)
    return _normalize(transformed)


def _symmetry_color(cells, original_color):
    shape = _normalize(cells)
    height = max(r for r, _ in shape) + 1
    width = max(c for _, c in shape) + 1

    horizontal = _transform(shape, "horizontal") == shape
    vertical = _transform(shape, "vertical") == shape
    half_turn = _transform(shape, "half_turn") == shape
    diagonal = (
        _transform(shape, "main_diagonal") == shape
        or _transform(shape, "anti_diagonal") == shape
    )

    # When both orthogonal axes exist, the parity of the bounding box tells
    # whether an axis runs through a cell row/column or between two of them.
    if horizontal and vertical:
        if height % 2 == 1 and width % 2 == 1:
            return 8
        if height % 2 == 1 and width % 2 == 0:
            return 3
        if height % 2 == 0 and width % 2 == 1:
            return 2
        return 4
    if vertical:
        return 2
    if horizontal:
        return 3
    if diagonal or half_turn:
        return 4

    # The visible examples do not specify a label for a wholly asymmetric
    # object, so avoid inventing a destructive recoloring for that case.
    return original_color


def solve(grid):
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    out = [row[:] for row in grid]
    seen = set()

    for r0 in range(rows):
        for c0 in range(cols):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue

            component = set()
            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            while queue:
                r, c = queue.popleft()
                component.add((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < rows
                        and 0 <= nc < cols
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            replacement = _symmetry_color(component, color)
            for r, c in component:
                out[r][c] = replacement

    return out
