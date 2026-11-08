from __future__ import annotations


def solve(grid):
    """Keep exactly the monochrome 4-connected components with 180° symmetry."""
    height = len(grid)
    width = len(grid[0]) if height else 0
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
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and (rr, cc) not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))

            min_r = min(r for r, _ in cells)
            min_c = min(c for _, c in cells)
            normalized = {(r - min_r, c - min_c) for r, c in cells}
            box_h = max(r for r, _ in normalized) + 1
            box_w = max(c for _, c in normalized) + 1
            rotated = {
                (box_h - 1 - r, box_w - 1 - c) for r, c in normalized
            }
            if normalized == rotated:
                for r, c in cells:
                    output[r][c] = color

    return output
