from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Replace the gray 2x2 marker with the four quadrant colors."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    if not height or any(len(row) != width for row in grid):
        raise ValueError("grid must be a non-empty rectangle")

    block = None
    for row in range(height - 1):
        for col in range(width - 1):
            if all(grid[row + dr][col + dc] == 8 for dr in (0, 1) for dc in (0, 1)):
                block = (row, col)
                break
        if block is not None:
            break
    if block is None:
        raise ValueError("no 2x2 gray marker found")

    top, left = block
    bottom, right = top + 1, left + 1
    quadrant_colors: dict[tuple[int, int], int] = {}

    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color in (0, 8):
                continue
            vertical = 0 if row < top else 1 if row > bottom else None
            horizontal = 0 if col < left else 1 if col > right else None
            if vertical is None or horizontal is None:
                raise ValueError("colored marker is not strictly in a marker quadrant")
            key = (vertical, horizontal)
            if key in quadrant_colors:
                raise ValueError("more than one colored marker in a quadrant")
            quadrant_colors[key] = color

    expected = {(0, 0), (0, 1), (1, 0), (1, 1)}
    if quadrant_colors.keys() != expected:
        raise ValueError("expected exactly one colored marker in each quadrant")

    output = [[0 for _ in range(width)] for _ in range(height)]
    for (dr, dc), color in quadrant_colors.items():
        output[top + dr][left + dc] = color
    return output
