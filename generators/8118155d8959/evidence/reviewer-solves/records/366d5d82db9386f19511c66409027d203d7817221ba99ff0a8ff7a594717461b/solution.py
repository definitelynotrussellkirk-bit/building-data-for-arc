from __future__ import annotations


def solve(grid):
    """Recolor the three 4-connected blue objects by ascending cell count."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)

    if len(components) != 3:
        raise ValueError(f"expected three blue components, found {len(components)}")

    components.sort(key=lambda cells: (len(cells), min(cells)))
    result = [row[:] for row in grid]
    for color, cells in zip((2, 3, 8), components):
        for row, col in cells:
            result[row][col] = color
    return result
