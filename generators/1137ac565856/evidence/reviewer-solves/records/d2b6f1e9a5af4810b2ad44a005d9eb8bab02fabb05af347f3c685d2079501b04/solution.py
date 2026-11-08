from collections import deque


def _components(grid, color):
    """Yield 4-connected components for one color as sets of (row, col)."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    unseen = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    while unseen:
        start = unseen.pop()
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= nr < height and 0 <= nc < width and (nr, nc) in unseen:
                    unseen.remove((nr, nc))
                    component.add((nr, nc))
                    queue.append((nr, nc))
        yield component


def solve(grid):
    """Return the smallest complete colored rectangular frame enclosing color 2, filled in."""
    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    if len(markers) != 1:
        raise ValueError(f"expected exactly one marker of color 2, found {len(markers)}")
    marker_r, marker_c = markers[0]

    candidates = []
    colors = {value for row in grid for value in row if value not in (0, 2)}
    for color in colors:
        for component in _components(grid, color):
            rows = [r for r, _ in component]
            cols = [c for _, c in component]
            top, bottom = min(rows), max(rows)
            left, right = min(cols), max(cols)
            if not (top < marker_r < bottom and left < marker_c < right):
                continue

            border = {
                (r, c)
                for r in range(top, bottom + 1)
                for c in range(left, right + 1)
                if r in (top, bottom) or c in (left, right)
            }
            if component != border:
                continue

            height = bottom - top + 1
            width = right - left + 1
            candidates.append((height * width, height, width, color))

    if not candidates:
        raise ValueError("no complete colored rectangular frame encloses the marker")

    _, height, width, color = min(candidates)
    return [[color for _ in range(width)] for _ in range(height)]
