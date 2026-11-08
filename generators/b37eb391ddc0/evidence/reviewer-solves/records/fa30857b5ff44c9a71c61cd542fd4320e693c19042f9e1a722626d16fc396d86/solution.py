"""Visible-only solver for the assigned blind ARC episode."""

from collections import Counter, deque
from typing import List, Sequence, Tuple

Grid = List[List[int]]


def _components8(grid: Sequence[Sequence[int]]) -> list[list[Tuple[int, int]]]:
    """Return 8-connected components of non-background cells."""
    h, w = len(grid), len(grid[0])
    seen: set[Tuple[int, int]] = set()
    components: list[list[Tuple[int, int]]] = []

    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            component: list[Tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                component.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == dc == 0:
                            continue
                        nr, nc = rr + dr, cc + dc
                        if (
                            0 <= nr < h
                            and 0 <= nc < w
                            and grid[nr][nc] != 0
                            and (nr, nc) not in seen
                        ):
                            seen.add((nr, nc))
                            queue.append((nr, nc))
            components.append(component)
    return components


def solve(grid: Grid) -> Grid:
    """
    Complete the embedded 2x3 (or rotated 3x2) rectangle.

    The relevant 8-connected component has five marked cells in two colors:
    three cells of the fill color form the alternating corners/centre of the
    rectangle, while two cells of another color act as distractors.  Fill the
    bounding rectangle of the three-cell color and leave all other cells alone.
    """
    out = [row[:] for row in grid]
    candidates: list[tuple[int, int, int, int, int]] = []

    for component in _components8(grid):
        counts = Counter(grid[r][c] for r, c in component)
        if len(component) != 5 or sorted(counts.values()) != [2, 3]:
            continue

        fill_color = next(color for color, count in counts.items() if count == 3)
        cells = [(r, c) for r, c in component if grid[r][c] == fill_color]
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        height, width = r1 - r0 + 1, c1 - c0 + 1
        if (height, width) not in {(2, 3), (3, 2)}:
            continue

        # The three clues occupy one checkerboard parity of the rectangle.
        local_parities = {(r - r0 + c - c0) % 2 for r, c in cells}
        if len(local_parities) != 1:
            continue
        candidates.append((r0, r1, c0, c1, fill_color))

    # The examples contain exactly one such component.  Requiring uniqueness
    # avoids changing unrelated coincidental patterns in a more cluttered grid.
    if len(candidates) == 1:
        r0, r1, c0, c1, fill_color = candidates[0]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = fill_color

    return out
