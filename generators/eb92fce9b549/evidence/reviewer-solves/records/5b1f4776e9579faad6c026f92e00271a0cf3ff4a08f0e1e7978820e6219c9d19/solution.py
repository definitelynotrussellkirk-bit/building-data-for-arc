"""Visible-example solution for the prepared eb92fce9b549 episode."""


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    objects = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + dr
                    next_col = current_col + dc
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))

            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            bbox_area = (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)
            objects.append((bbox_area, min(rows), min(cols), cells))

    # The visible examples use distinct bounding-box areas.  Top-left position
    # is only a deterministic tie-breaker for an otherwise unseen tie case.
    objects.sort(key=lambda item: (-item[0], item[1], item[2]))
    output = [[0 for _ in range(width)] for _ in range(height)]
    for rank, (_, _, _, cells) in enumerate(objects, start=2):
        for row, col in cells:
            output[row][col] = rank
    return output
