from collections import deque


def solve(grid):
    """Encode nonzero 4-connected components as one area-sorted color row."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    items = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            area = 0
            while queue:
                r, c = queue.popleft()
                area += 1
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            items.append((area, color))

    items.sort(key=lambda item: (-item[0], item[1]))
    row = [color for area, color in items for _ in range(area)]
    return [row or [0]]
