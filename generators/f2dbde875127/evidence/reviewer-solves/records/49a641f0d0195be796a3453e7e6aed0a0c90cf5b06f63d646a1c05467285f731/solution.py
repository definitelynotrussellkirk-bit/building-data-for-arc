"""Standalone solution inferred from the four public demonstrations."""
from copy import deepcopy

_KEYS = (2, 3, 4, 5)
_TURNS = {2: 0, 3: 1, 4: 2, 5: 3}


def _frame_components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    boxes = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and grid[nr][nc] == 1 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            boxes.append((
                min(r for r, _ in cells),
                min(c for _, c in cells),
                max(r for r, _ in cells),
                max(c for _, c in cells),
            ))
    return sorted(boxes)


def _rotate_clockwise(patch, turns):
    result = [row[:] for row in patch]
    for _ in range(turns % 4):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def solve(grid):
    """Rotate each framed object according to its key, then floor-center it."""
    out = deepcopy(grid)
    for top, left, bottom, right in _frame_components(grid):
        key_cells = [grid[top - 1][col] for col in range(left, right + 1)
                     if top > 0 and grid[top - 1][col] in _KEYS]
        if len(key_cells) != 1:
            raise ValueError("each frame must have exactly one key immediately above it")
        key = key_cells[0]
        points = [(row, col)
                  for row in range(top + 1, bottom)
                  for col in range(left + 1, right)
                  if grid[row][col] not in (0, 1)]
        if not points:
            raise ValueError("each frame must contain a nonempty object")

        obj_top = min(row for row, _ in points)
        obj_bottom = max(row for row, _ in points)
        obj_left = min(col for _, col in points)
        obj_right = max(col for _, col in points)
        patch = [row[obj_left:obj_right + 1]
                 for row in grid[obj_top:obj_bottom + 1]]
        patch = _rotate_clockwise(patch, _TURNS[key])

        for row in range(top + 1, bottom):
            for col in range(left + 1, right):
                out[row][col] = 0
        interior_height = bottom - top - 1
        interior_width = right - left - 1
        place_top = top + 1 + (interior_height - len(patch)) // 2
        place_left = left + 1 + (interior_width - len(patch[0])) // 2
        for dr, row_values in enumerate(patch):
            for dc, value in enumerate(row_values):
                if value != 0:
                    out[place_top + dr][place_left + dc] = value
    return out
