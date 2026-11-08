from collections import deque


def _frame_components(grid):
    """Return the bounding boxes of the three 4-connected color-1 frames."""
    h, w = len(grid), len(grid[0])
    seen = set()
    boxes = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            boxes.append((min(rows), min(cols), max(rows), max(cols)))
    return sorted(boxes, key=lambda box: (box[1], box[0]))


def _symmetry_signature(grid, box):
    """Classify the tight binary motif by left/right and up/down reflection."""
    r0, c0, r1, c1 = box
    occupied = [
        (r, c)
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
        if grid[r][c] not in (0, 1)
    ]
    top = min(r for r, _ in occupied)
    bottom = max(r for r, _ in occupied)
    left = min(c for _, c in occupied)
    right = max(c for _, c in occupied)
    shape = {
        (r - top, c - left)
        for r, c in occupied
    }
    height = bottom - top + 1
    width = right - left + 1
    left_right = shape == {(r, width - 1 - c) for r, c in shape}
    up_down = shape == {(height - 1 - r, c) for r, c in shape}
    return left_right, up_down


def solve(grid):
    signatures = [
        _symmetry_signature(grid, box)
        for box in _frame_components(grid)
    ]
    return [
        [2 if signatures[r] == signatures[c] else 0 for c in range(3)]
        for r in range(3)
    ]
