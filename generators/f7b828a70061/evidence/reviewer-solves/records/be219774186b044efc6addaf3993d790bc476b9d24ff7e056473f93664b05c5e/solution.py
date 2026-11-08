from __future__ import annotations

from collections import deque

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _rotate(grid: list[list[int]], command: int) -> list[list[int]]:
    if command == 2:
        return [row[:] for row in grid]
    if command == 3:
        return [list(row) for row in zip(*grid[::-1])]
    if command == 4:
        return [row[::-1] for row in grid[::-1]]
    return [list(row) for row in zip(*grid)][::-1]


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Crop the largest nonzero component, then rotate by the corner command."""
    if not grid or not grid[0]:
        return []

    command = grid[0][0]
    cleaned = [row[:] for row in grid]
    cleaned[0][0] = 0
    height = len(cleaned)
    width = len(cleaned[0])

    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for start_r in range(height):
        for start_c in range(width):
            if cleaned[start_r][start_c] == 0 or (start_r, start_c) in seen:
                continue
            queue = deque([(start_r, start_c)])
            seen.add((start_r, start_c))
            component: list[tuple[int, int]] = []
            while queue:
                row, col = queue.popleft()
                component.append((row, col))
                for dr, dc in _CARDINAL:
                    nr, nc = row + dr, col + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and cleaned[nr][nc] != 0 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(component)

    if not components:
        return []
    main = min(components, key=lambda cells: (-len(cells), min(cells)))
    top = min(row for row, _ in main)
    bottom = max(row for row, _ in main)
    left = min(col for _, col in main)
    right = max(col for _, col in main)
    crop = [row[left:right + 1] for row in cleaned[top:bottom + 1]]
    return _rotate(crop, command)
