"""Visible-example solution for c00a9bcded8e."""
from __future__ import annotations


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
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
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            top, bottom = min(rows), max(rows)
            left, right = min(cols), max(cols)
            box_height = bottom - top + 1
            box_width = right - left + 1
            result.append(
                {
                    "color": color,
                    "size": len(cells),
                    "area": box_height * box_width,
                    "center_row": (top + bottom) / 2,
                    "center_col": (left + right) / 2,
                }
            )
    return result


def solve(grid):
    # The intended objects are the large, completely filled rectangles.  The
    # two dense distractor colors form irregular components instead.
    rectangles = [
        component
        for component in _components(grid)
        if component["size"] >= 9 and component["size"] == component["area"]
    ]
    rectangles.sort(key=lambda component: component["center_row"])

    rows = []
    last_center = None
    for rectangle in rectangles:
        center = rectangle["center_row"]
        if last_center is None or center - last_center >= 4:
            rows.append([])
        rows[-1].append(rectangle)
        last_center = center

    answer = []
    for row in rows:
        row.sort(key=lambda component: component["center_col"])
        answer.append([component["color"] for component in row])
    return answer
