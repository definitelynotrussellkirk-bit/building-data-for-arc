from collections import Counter


def solve(grid):
    """Return the exact nonzero component crop that occurs more than once."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = [[False] * width for _ in range(height)]
    crops = []

    for start_r in range(height):
        for start_c in range(width):
            if seen[start_r][start_c] or grid[start_r][start_c] == 0:
                continue

            stack = [(start_r, start_c)]
            seen[start_r][start_c] = True
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = row + dr, col + dc
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and not seen[rr][cc]
                        and grid[rr][cc] != 0
                    ):
                        seen[rr][cc] = True
                        stack.append((rr, cc))

            min_r = min(row for row, _ in cells)
            max_r = max(row for row, _ in cells)
            min_c = min(col for _, col in cells)
            max_c = max(col for _, col in cells)
            crop = tuple(
                tuple(grid[row][min_c : max_c + 1])
                for row in range(min_r, max_r + 1)
            )
            crops.append(crop)

    counts = Counter(crops)
    for crop in crops:
        if counts[crop] > 1:
            return [list(row) for row in crop]

    raise ValueError("No repeated component crop found")
