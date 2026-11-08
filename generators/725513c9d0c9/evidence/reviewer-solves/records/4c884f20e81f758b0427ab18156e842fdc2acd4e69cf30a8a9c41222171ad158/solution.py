from __future__ import annotations


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    """Return 4-connected components of non-background, non-marker cells."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] in (0, 8) or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] in (0, 8):
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
            components.append(cells)

    return components


def solve(grid: list[list[int]]) -> list[list[int]]:
    marker = next(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 8
    )

    candidates = [
        cells
        for cells in _components(grid)
        if any(abs(row - marker[0]) + abs(col - marker[1]) == 1 for row, col in cells)
    ]
    if len(candidates) != 1:
        raise ValueError(f"expected one component cardinally adjacent to marker, got {len(candidates)}")

    target = candidates[0]
    target_cells = set(target)
    min_row = min(row for row, _ in target)
    max_row = max(row for row, _ in target)
    min_col = min(col for _, col in target)
    max_col = max(col for _, col in target)

    crop = [
        [
            grid[row][col] if (row, col) in target_cells else 0
            for col in range(min_col, max_col + 1)
        ]
        for row in range(min_row, max_row + 1)
    ]

    scaled: list[list[int]] = []
    for row in crop:
        doubled_row = [value for value in row for _ in range(2)]
        scaled.extend([doubled_row[:], doubled_row[:]])
    return scaled
