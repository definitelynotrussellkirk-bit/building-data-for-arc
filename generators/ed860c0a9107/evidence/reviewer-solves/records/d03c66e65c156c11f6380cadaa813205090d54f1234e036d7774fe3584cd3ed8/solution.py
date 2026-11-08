from collections import Counter, deque


def solve(grid):
    """Overlay separated equal-size panels in reading order; zero is transparent."""
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]

    seen = set()
    panels = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == background or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != background
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            top = min(r for r, _ in cells)
            bottom = max(r for r, _ in cells)
            left = min(c for _, c in cells)
            right = max(c for _, c in cells)
            panel = [input_row[left : right + 1] for input_row in grid[top : bottom + 1]]
            panels.append((top, left, panel))

    if not panels:
        return []

    panels.sort(key=lambda item: (item[0], item[1]))
    panel_height = len(panels[0][2])
    panel_width = len(panels[0][2][0])
    output = [[0 for _ in range(panel_width)] for _ in range(panel_height)]

    for local_row in range(panel_height):
        for local_col in range(panel_width):
            for _, _, panel in panels:
                value = panel[local_row][local_col]
                if value != 0:
                    output[local_row][local_col] = value
                    break

    return output
