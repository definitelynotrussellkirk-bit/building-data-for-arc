from collections import Counter, deque


def _components(grid, color):
    height = len(grid)
    width = len(grid[0]) if height else 0
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == color}
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        component = [start]
        while queue:
            r, c = queue.popleft()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in unseen:
                    unseen.remove((nr, nc))
                    queue.append((nr, nc))
                    component.append((nr, nc))
        components.append(component)
    return components


def solve(grid):
    """Keep each color's selected component and replace it by a left-expanded bbox."""
    if not grid:
        return []
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("expected a nonempty rectangular grid")

    counts = Counter(cell for row in grid for cell in row)
    background = max(counts, key=lambda color: counts[color])
    result = [row[:] for row in grid]

    for color in sorted(c for c in counts if c != background):
        components = _components(grid, color)
        if len(components) <= 1:
            continue

        # The second example has equally large components and retains the one
        # farther down/right.  The visible evidence supports top-left r+c as
        # the tie-break; row and column provide deterministic residual ties.
        def rank(component):
            min_r = min(r for r, _ in component)
            min_c = min(c for _, c in component)
            return (len(component), min_r + min_c, min_r, min_c)

        winner = max(components, key=rank)
        min_r = min(r for r, _ in winner)
        max_r = max(r for r, _ in winner)
        min_c = min(c for _, c in winner)
        max_c = max(c for _, c in winner)

        for r in range(len(grid)):
            for c in range(width):
                if result[r][c] == color:
                    result[r][c] = background

        for r in range(min_r, max_r + 1):
            for c in range(max(0, min_c - 1), max_c + 1):
                result[r][c] = color

    return result
