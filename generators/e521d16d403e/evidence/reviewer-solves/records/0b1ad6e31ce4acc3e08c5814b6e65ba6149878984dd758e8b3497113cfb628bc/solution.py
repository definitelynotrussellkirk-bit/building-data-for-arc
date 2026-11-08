"""Crop the largest nontrivial left-right-symmetric colored component."""
from collections import deque


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    choices = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            todo = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while todo:
                r, c = todo.popleft()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            top = min(r for r, c in cells)
            bottom = max(r for r, c in cells)
            left = min(c for r, c in cells)
            right = max(c for r, c in cells)
            crop = [list(line[left:right + 1]) for line in grid[top:bottom + 1]]
            if right > left and all(line == line[::-1] for line in crop):
                choices.append((len(cells), crop))
    if not choices:
        raise ValueError('No qualifying object; this case is not supported by the visible demonstrations')
    return max(choices, key=lambda item: item[0])[1]
