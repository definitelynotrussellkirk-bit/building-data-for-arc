"""Visible-example solution for the prepared ARC task."""

from collections import deque


def _components(grid, color):
    """Return four-connected components of *color* as coordinate sets."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == color}
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        component = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        components.append(component)
    return components


def _normalized(component):
    min_r = min(r for r, _ in component)
    min_c = min(c for _, c in component)
    return frozenset((r - min_r, c - min_c) for r, c in component)


def solve(grid):
    """Recolor candidate components by exact, orientation-sensitive template match."""
    output = [row[:] for row in grid]
    templates = _components(grid, 5)
    if len(templates) != 1:
        raise ValueError(f"expected exactly one color-5 template, found {len(templates)}")
    template_shape = _normalized(templates[0])

    for candidate in _components(grid, 2):
        replacement = 4 if _normalized(candidate) == template_shape else 1
        for r, c in candidate:
            output[r][c] = replacement
    return output
