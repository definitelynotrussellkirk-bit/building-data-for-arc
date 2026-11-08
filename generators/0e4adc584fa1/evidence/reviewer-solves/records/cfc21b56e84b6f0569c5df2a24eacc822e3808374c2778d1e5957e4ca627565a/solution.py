from __future__ import annotations


def _rotate_clockwise(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Remove isolated control cells, crop the object, and apply its coded turn."""
    if not grid or not grid[0]:
        return []
    height, width = len(grid), len(grid[0])
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    controls: list[tuple[int, int]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] not in (1, 2, 3, 4):
                continue
            isolated = all(
                not (0 <= row + dr < height and 0 <= col + dc < width)
                or grid[row + dr][col + dc] == 0
                for dr, dc in directions
            )
            if isolated:
                controls.append((row, col))

    if not controls:
        raise ValueError("no isolated control cell")
    control_row, control_col = controls[-1]
    turns = grid[control_row][control_col] - 1
    control_set = set(controls)

    object_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0 and (row, col) not in control_set
    ]
    if not object_cells:
        return []

    top = min(row for row, _ in object_cells)
    bottom = max(row for row, _ in object_cells)
    left = min(col for _, col in object_cells)
    right = max(col for _, col in object_cells)
    result = [
        [0 if (row, col) in control_set else grid[row][col]
         for col in range(left, right + 1)]
        for row in range(top, bottom + 1)
    ]
    for _ in range(turns % 4):
        result = _rotate_clockwise(result)
    return result
