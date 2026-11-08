"""Visible-example solution for blind task cc100a8ad437."""

from collections import deque


def _components(grid):
    """Return 4-connected nonzero monochrome components."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            points = []
            while stack:
                rr, cc = stack.pop()
                points.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, points))
    return result


def solve(grid):
    """Find right-panel copies of left-panel shapes and box them in azure."""
    h, w = len(grid), len(grid[0])
    separator = next(
        c for c in range(w) if all(grid[r][c] == 9 for r in range(h))
    )
    left = [row[:separator] for row in grid]
    right = [row[separator + 1 :] for row in grid]
    rw = len(right[0])
    out = [[0] * rw for _ in range(h)]

    templates = []
    for color, points in _components(left):
        top = min(r for r, _ in points)
        bottom = max(r for r, _ in points)
        left_col = min(c for _, c in points)
        right_col = max(c for _, c in points)
        mask = {(r - top, c - left_col) for r, c in points}
        templates.append((color, bottom - top + 1, right_col - left_col + 1, mask))

    for color, th, tw, mask in templates:
        for top in range(h - th + 1):
            for left_col in range(rw - tw + 1):
                # Other colors are annotation/noise.  Only the template color's
                # occupancy inside the bounding box must match exactly.
                if all(
                    ((right[top + dr][left_col + dc] == color) == ((dr, dc) in mask))
                    for dr in range(th)
                    for dc in range(tw)
                ):
                    for dc in range(tw):
                        out[top][left_col + dc] = 8
                        out[top + th - 1][left_col + dc] = 8
                    for dr in range(th):
                        out[top + dr][left_col] = 8
                        out[top + dr][left_col + tw - 1] = 8

    return out
