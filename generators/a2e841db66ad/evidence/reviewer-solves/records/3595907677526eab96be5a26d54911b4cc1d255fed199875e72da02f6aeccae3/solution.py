from __future__ import annotations


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    """Return same-color 4-connected components below the header row."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(1, height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        1 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return components


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not grid or not grid[0]:
        raise ValueError("expected a nonempty grid")

    wanted_height = sum(value == 1 for value in grid[0])
    matches: list[list[tuple[int, int]]] = []
    for cells in _components(grid):
        rows = [row for row, _ in cells]
        if max(rows) - min(rows) + 1 == wanted_height:
            matches.append(cells)
    if len(matches) != 1:
        raise ValueError(f"expected one height-{wanted_height} component, found {len(matches)}")

    cells = matches[0]
    row0 = min(row for row, _ in cells)
    row1 = max(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    col1 = max(col for _, col in cells)
    output = [[0 for _ in range(col1 - col0 + 1)] for _ in range(row1 - row0 + 1)]
    for row, col in cells:
        output[row - row0][col - col0] = 8
    return output
