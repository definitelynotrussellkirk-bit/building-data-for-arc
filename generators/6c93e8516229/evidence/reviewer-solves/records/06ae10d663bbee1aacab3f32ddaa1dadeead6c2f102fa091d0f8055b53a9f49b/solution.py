from collections import deque


ORTHOGONAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _components(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue

            component = []
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                cell = queue.popleft()
                component.append(cell)
                for dr, dc in ORTHOGONAL:
                    neighbor = (cell[0] + dr, cell[1] + dc)
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            yield component


def _turn_count(component):
    """Return the number of direction changes along a non-branching path."""
    cells = set(component)
    neighbors = {
        cell: [
            (cell[0] + dr, cell[1] + dc)
            for dr, dc in ORTHOGONAL
            if (cell[0] + dr, cell[1] + dc) in cells
        ]
        for cell in cells
    }
    endpoints = [cell for cell, adjacent in neighbors.items() if len(adjacent) == 1]
    if len(endpoints) != 2 or any(len(adjacent) > 2 for adjacent in neighbors.values()):
        return None

    previous = None
    current = endpoints[0]
    previous_direction = None
    turns = 0
    while current != endpoints[1]:
        candidates = [cell for cell in neighbors[current] if cell != previous]
        if not candidates:
            return None
        nxt = candidates[0]
        direction = (nxt[0] - current[0], nxt[1] - current[1])
        if previous_direction is not None and direction != previous_direction:
            turns += 1
        previous, current = current, nxt
        previous_direction = direction
    return turns


def solve(grid):
    output = [row[:] for row in grid]

    for component in _components(grid):
        cells = set(component)
        degrees = []
        for row, col in component:
            degrees.append(
                sum((row + dr, col + dc) in cells for dr, dc in ORTHOGONAL)
            )

        # The visible examples divide the gray objects into three shape classes:
        # T-like objects (a degree-3 junction), two-turn paths, and everything else.
        if 3 in degrees:
            color = 2
        elif _turn_count(component) == 2:
            color = 6
        else:
            color = 1

        for row, col in component:
            output[row][col] = color

    return output
