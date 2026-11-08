from __future__ import annotations


def _nested_colors(grid: list[list[int]]) -> list[int]:
    """Read uniform nested rectangles from the outside toward the center."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be nonempty and rectangular")

    top, left = 0, 0
    bottom, right = len(grid) - 1, len(grid[0]) - 1
    colors: list[int] = []

    while True:
        color = grid[top][left]
        colors.append(color)
        different = [
            (row, col)
            for row in range(top, bottom + 1)
            for col in range(left, right + 1)
            if grid[row][col] != color
        ]
        if not different:
            return colors

        next_top = min(row for row, _ in different)
        next_left = min(col for _, col in different)
        next_bottom = max(row for row, _ in different)
        next_right = max(col for _, col in different)
        if not (top < next_top <= next_bottom < bottom and left < next_left <= next_right < right):
            raise ValueError("input is not a hierarchy of strictly nested rectangles")

        # Everything exposed around the next bounding box must belong to this layer.
        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                inside = next_top <= row <= next_bottom and next_left <= col <= next_right
                if not inside and grid[row][col] != color:
                    raise ValueError("nonuniform rectangular layer")

        top, left, bottom, right = next_top, next_left, next_bottom, next_right


def solve(grid: list[list[int]]) -> list[list[int]]:
    colors = _nested_colors(grid)  # outside -> inside
    side = 2 * len(colors) - 1
    center = side // 2
    return [
        [colors[max(abs(row - center), abs(col - center))] for col in range(side)]
        for row in range(side)
    ]
