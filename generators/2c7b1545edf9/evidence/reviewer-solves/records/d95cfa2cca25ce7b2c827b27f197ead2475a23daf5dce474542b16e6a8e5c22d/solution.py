from collections import deque


def _components(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, cells))

    return components


def _diameter(cells):
    cell_set = set(cells)
    best = 0
    for start in cells:
        queue = deque([(start, 0)])
        reached = {start}
        while queue:
            (row, col), distance = queue.popleft()
            best = max(best, distance)
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (row + dr, col + dc)
                if nxt in cell_set and nxt not in reached:
                    reached.add(nxt)
                    queue.append((nxt, distance + 1))
    return best


def _score(cells):
    cell_set = set(cells)
    shared_edges = sum(
        ((row + 1, col) in cell_set) + ((row, col + 1) in cell_set)
        for row, col in cells
    )
    perimeter = 4 * len(cells) - 2 * shared_edges
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    box_area = (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)

    # The demonstrations consistently select the largest component.  The first
    # demonstration has an equal-size distractor, distinguished by its longer
    # one-cell path; perimeter and graph diameter preserve that distinction and
    # resolve the analogous equal-size query case without relying on color.
    return (len(cells), perimeter, _diameter(cells), box_area)


def solve(grid):
    components = _components(grid)
    if not components:
        return []

    color, cells = max(components, key=lambda item: _score(item[1]))
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    cell_set = set(cells)

    return [
        [color if (row, col) in cell_set else 0 for col in range(left, right + 1)]
        for row in range(top, bottom + 1)
    ]
