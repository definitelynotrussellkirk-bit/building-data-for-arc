from collections import deque


def _yellow_components(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 4 or (row, col) in seen:
                continue
            component = []
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 4
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(component)
    return components


def _enclosed_zero_regions(grid, component):
    cells = set(component)
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)

    seen = set()
    holes = 0
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            if grid[row][col] != 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            touches_box_edge = False
            while queue:
                r, c = queue.popleft()
                if r in (r0, r1) or c in (c0, c1):
                    touches_box_edge = True
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        r0 <= nr <= r1
                        and c0 <= nc <= c1
                        and grid[nr][nc] == 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            if not touches_box_edge:
                holes += 1
    return holes


def solve(grid):
    result = [row[:] for row in grid]
    color_for_holes = {0: 2, 1: 3, 2: 8}
    for component in _yellow_components(grid):
        holes = _enclosed_zero_regions(grid, component)
        replacement = color_for_holes.get(holes, 4)
        for row, col in component:
            result[row][col] = replacement
    return result
