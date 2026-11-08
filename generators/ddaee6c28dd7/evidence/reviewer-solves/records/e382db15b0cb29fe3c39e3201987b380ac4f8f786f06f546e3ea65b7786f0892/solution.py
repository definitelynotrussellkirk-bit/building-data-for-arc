from collections import deque


def _components(grid):
    """Return 4-connected nonzero components as lists of (row, col)."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(cells)
    return components


def solve(grid):
    """Crop the widest colored object and recolor its cells to 8."""
    components = _components(grid)
    if not components:
        return []

    def bounds(cells):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        return min(rows), max(rows), min(cols), max(cols)

    # All visible demonstrations have one unique widest object.  Secondary
    # keys make behavior deterministic without affecting those examples.
    chosen = max(
        components,
        key=lambda cells: (
            bounds(cells)[3] - bounds(cells)[2] + 1,
            len(cells),
            bounds(cells)[1] - bounds(cells)[0] + 1,
        ),
    )
    r0, r1, c0, c1 = bounds(chosen)
    selected = set(chosen)
    return [
        [8 if (row, col) in selected else 0 for col in range(c0, c1 + 1)]
        for row in range(r0, r1 + 1)
    ]
