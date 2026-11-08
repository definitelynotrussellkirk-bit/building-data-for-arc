from __future__ import annotations

from collections import deque


def _components(grid, col_lo, col_hi):
    """Return monochrome 4-connected components inside one panel."""
    height = len(grid)
    seen = set()
    components = []
    for row in range(height):
        for col in range(col_lo, col_hi + 1):
            color = grid[row][col]
            if color == 0 or color == 5 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and col_lo <= nc <= col_hi
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(cells)
    return components


def _row_profile(cells):
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    return [sum(row == target for row, _ in cells) for target in range(top, bottom + 1)]


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    dividers = [
        col for col in range(width) if all(grid[row][col] == 5 for row in range(height))
    ]
    if not dividers:
        raise ValueError("no full-height gray divider")
    divider = dividers[0]

    left_objects = _components(grid, 0, divider - 1)
    right_objects = _components(grid, divider + 1, width - 1)
    if not left_objects or not right_objects:
        raise ValueError("both panels need an object")

    # The examples have one object per panel; choosing the largest also handles
    # harmless smaller marks without changing the inferred transformation.
    left = max(left_objects, key=len)
    right = max(right_objects, key=len)
    left_profile = _row_profile(left)
    right_profile = _row_profile(right)

    length = max(len(left_profile), len(right_profile))
    left_profile += [0] * (length - len(left_profile))
    right_profile += [0] * (length - len(right_profile))
    difference = [abs(a - b) for a, b in zip(left_profile, right_profile)]

    out_width = max(1, max(difference))
    return [
        [8 if col < count else 0 for col in range(out_width)]
        for count in difference
    ]
