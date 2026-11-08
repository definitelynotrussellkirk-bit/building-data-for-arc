from __future__ import annotations

from collections import deque


def _components_of_eight(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    """Return the 4-connected color-8 components."""
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8}
    components: list[set[tuple[int, int]]] = []
    while unseen:
        start = unseen.pop()
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (r + dr, c + dc)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill nested qualifying color-8 boxes with the left-column palette."""
    h, w = len(grid), len(grid[0])
    output = [row[:] for row in grid]

    # The palette is the contiguous nonzero prefix of column 0.
    palette: list[int] = []
    for row in grid:
        value = row[0]
        if value == 0:
            break
        palette.append(value)

    boxes: list[tuple[int, int, int, int]] = []
    for component in _components_of_eight(grid):
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(cols), max(cols)
        box_h = r1 - r0 + 1
        box_w = c1 - c0 + 1
        perimeter_size = 2 * (box_h + box_w) - 4
        # The first training example shows that exact outline placement is not
        # required: component size relative to its bounding box is decisive.
        if box_h >= 3 and box_w >= 3 and len(component) == perimeter_size:
            boxes.append((r0, c0, r1, c1))

    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            depth = sum(r0 < r < r1 and c0 < c < c1 for r0, c0, r1, c1 in boxes)
            if 1 <= depth <= len(palette):
                output[r][c] = palette[depth - 1]

    return output
