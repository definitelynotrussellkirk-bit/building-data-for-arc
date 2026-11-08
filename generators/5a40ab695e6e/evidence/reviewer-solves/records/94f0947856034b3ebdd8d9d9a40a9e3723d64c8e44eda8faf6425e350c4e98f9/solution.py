"""Visible-example solution for the generated symmetry recolor puzzle."""
from __future__ import annotations


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            min_r = min(r for r, _ in cells)
            min_c = min(c for _, c in cells)
            mask = {(r - min_r, c - min_c) for r, c in cells}
            box_h = max(r for r, _ in mask)
            box_w = max(c for _, c in mask)
            left_right = {(r, box_w - c) for r, c in mask} == mask
            up_down = {(box_h - r, c) for r, c in mask} == mask

            if left_right and up_down:
                result_color = 2
            elif left_right:
                result_color = 3
            elif up_down:
                result_color = 4
            else:
                result_color = 6

            for r, c in cells:
                output[r][c] = result_color

    return output
