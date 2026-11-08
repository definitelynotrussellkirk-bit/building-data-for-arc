from collections import Counter, deque

DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid, background):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == background:
                continue
            color = grid[r][c]
            seen.add((r, c))
            queue = deque([(r, c)])
            cells = set()
            while queue:
                rr, cc = queue.popleft()
                cells.add((rr, cc))
                for dr, dc in DIRS:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            out.append(cells)
    return out


def _is_closed(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    top, bottom = min(rows), max(rows)
    left, right = min(cols), max(cols)
    gaps = {
        (r, c)
        for r in range(top, bottom + 1)
        for c in range(left, right + 1)
        if (r, c) not in cells
    }
    if not gaps:
        return True
    while gaps:
        start = min(gaps)
        gaps.remove(start)
        queue = deque([start])
        touches_bbox_boundary = False
        while queue:
            r, c = queue.popleft()
            if r in (top, bottom) or c in (left, right):
                touches_bbox_boundary = True
            for dr, dc in DIRS:
                nxt = (r + dr, c + dc)
                if nxt in gaps:
                    gaps.remove(nxt)
                    queue.append(nxt)
        if not touches_bbox_boundary:
            return True
    return False


def solve(grid):
    h, w = len(grid), len(grid[0])
    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]
    answer = [[background for _ in range(w)] for _ in range(h)]
    for cells in _components(grid, background):
        cols = [c for _, c in cells]
        left, right = min(cols), max(cols)
        width = right - left + 1
        closed = _is_closed(cells)
        destination_left = 0 if closed else w - width
        color = 2 if closed else 3
        for r, c in cells:
            answer[r][destination_left + c - left] = color
    return answer
