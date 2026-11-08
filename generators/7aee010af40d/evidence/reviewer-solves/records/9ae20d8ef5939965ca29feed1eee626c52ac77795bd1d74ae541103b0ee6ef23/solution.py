from __future__ import annotations


def _orange_components(grid):
    """Return 4-connected components of orange (7) cells."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 7 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 7
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(sorted(cells))
    return components


def solve(grid):
    """Crop the smallest orange object and recolor its occupied cells cyan."""
    components = _orange_components(grid)
    if not components:
        return []
    target = min(components, key=lambda cells: (len(cells), cells[0]))
    top = min(row for row, _ in target)
    bottom = max(row for row, _ in target)
    left = min(col for _, col in target)
    right = max(col for _, col in target)
    target_set = set(target)
    return [
        [8 if (row, col) in target_set else 0 for col in range(left, right + 1)]
        for row in range(top, bottom + 1)
    ]
