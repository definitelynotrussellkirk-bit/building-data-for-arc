from collections import deque


def _components(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    result = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            cells = []
            queue = deque([(sr, sc)])
            seen.add((sr, sc))
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append((color, cells))
    return result


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _is_frame(cells):
    r0, c0, r1, c1 = _bbox(cells)
    if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
        return False
    outline = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    return set(cells) == outline


def solve(grid):
    """Move the row-major-last non-frame component into the frame center."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    objects = _components(grid)
    frame_color, frame_cells = next(obj for obj in objects if _is_frame(obj[1]))
    nonframes = [obj for obj in objects if obj[1] is not frame_cells and not _is_frame(obj[1])]
    selected_color, selected_cells = nonframes[-1]

    sr0, sc0, sr1, sc1 = _bbox(selected_cells)
    shape = [(r - sr0, c - sc0) for r, c in selected_cells]
    shape_h = sr1 - sr0 + 1
    shape_w = sc1 - sc0 + 1

    fr0, fc0, fr1, fc1 = _bbox(frame_cells)
    interior_h = fr1 - fr0 - 1
    interior_w = fc1 - fc0 - 1
    top = fr0 + 1 + (interior_h - shape_h) // 2
    left = fc0 + 1 + (interior_w - shape_w) // 2

    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, c in frame_cells:
        out[r][c] = frame_color
    for dr, dc in shape:
        out[top + dr][left + dc] = selected_color
    return out
