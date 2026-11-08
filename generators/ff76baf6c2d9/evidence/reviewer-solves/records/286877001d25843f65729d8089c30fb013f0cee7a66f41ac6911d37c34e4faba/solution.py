from collections import deque


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc, grid[rr][cc]))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == dc == 0:
                            continue
                        nr, nc = rr + dr, cc + dc
                        if (
                            0 <= nr < h
                            and 0 <= nc < w
                            and grid[nr][nc] != 0
                            and (nr, nc) not in seen
                        ):
                            seen.add((nr, nc))
                            q.append((nr, nc))
            result.append(cells)
    return result


def _transforms(dr, dc):
    # Identity first: preserve the demonstrated orientation whenever possible.
    candidates = (
        (dr, dc),
        (dr, -dc),
        (-dr, dc),
        (-dr, -dc),
        (dc, -dr),
        (-dc, dr),
        (dc, dr),
        (-dc, -dr),
    )
    out = []
    for item in candidates:
        if item not in out:
            out.append(item)
    return out


def solve(grid):
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    components = _components(grid)

    singleton_positions = {}
    for cells in components:
        if len(cells) == 1:
            r, c, color = cells[0]
            singleton_positions.setdefault(color, []).append((r, c))

    templates = []
    for cells in components:
        if len(cells) <= 1:
            continue
        colors = {color for _, _, color in cells}
        for anchor_color in colors & singleton_positions.keys():
            anchors = [(r, c) for r, c, color in cells if color == anchor_color]
            if len(anchors) != 1:
                continue
            ar, ac = anchors[0]
            payload = [
                (r - ar, c - ac, color)
                for r, c, color in cells
                if (r, c) != (ar, ac)
            ]
            templates.append((anchor_color, payload))

    for anchor_color, payload in templates:
        for ar, ac in singleton_positions[anchor_color]:
            chosen = None
            for transform_index in range(8):
                stamped = []
                valid = True
                for dr, dc, color in payload:
                    options = _transforms(dr, dc)
                    if transform_index >= len(options):
                        valid = False
                        break
                    tr, tc = options[transform_index]
                    rr, cc = ar + tr, ac + tc
                    if not (0 <= rr < h and 0 <= cc < w):
                        valid = False
                        break
                    if out[rr][cc] != 0:
                        valid = False
                        break
                    stamped.append((rr, cc, color))
                if valid:
                    chosen = stamped
                    break
            if chosen is not None:
                for r, c, color in chosen:
                    out[r][c] = color

    return out
