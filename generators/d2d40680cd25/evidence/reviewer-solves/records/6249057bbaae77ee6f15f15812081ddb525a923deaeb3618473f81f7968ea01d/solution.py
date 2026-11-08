"""Visible-example solution for rigid downward gravity around a fixed cyan wall."""
from __future__ import annotations

from collections import deque


_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid):
    """Return same-colour 4-connected non-background components."""
    height, width = len(grid), len(grid[0])
    seen = set()
    found = []
    for row in range(height):
        for col in range(width):
            colour = grid[row][col]
            if colour == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = set()
            while queue:
                current = queue.popleft()
                cells.add(current)
                r, c = current
                for dr, dc in _NEIGHBORS:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == colour
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            found.append((colour, cells))
    return found


def solve(grid):
    """Drop each non-cyan rigid component until blocked; keep colour 8 fixed."""
    out = [list(row) for row in grid]
    if not out or not out[0]:
        return out
    height, width = len(out), len(out[0])

    # Recompute components after each sweep.  Processing lower bodies first makes
    # upper bodies settle onto their final positions, including stacked bars.
    for _ in range(3 * height * width):
        bodies = [item for item in _components(out) if item[0] != 8]
        bodies.sort(key=lambda item: max(r for r, _ in item[1]), reverse=True)
        changed = False

        for colour, original in bodies:
            occupied = {
                (r, c)
                for r, row in enumerate(out)
                for c, value in enumerate(row)
                if value != 0 and (r, c) not in original
            }
            shifted = set(original)
            while True:
                candidate = {(r + 1, c) for r, c in shifted}
                if any(r >= height or not (0 <= c < width) for r, c in candidate):
                    break
                if candidate & occupied:
                    break
                shifted = candidate

            if shifted != original:
                for r, c in original:
                    out[r][c] = 0
                for r, c in shifted:
                    out[r][c] = colour
                changed = True

        if not changed:
            break
    return out
