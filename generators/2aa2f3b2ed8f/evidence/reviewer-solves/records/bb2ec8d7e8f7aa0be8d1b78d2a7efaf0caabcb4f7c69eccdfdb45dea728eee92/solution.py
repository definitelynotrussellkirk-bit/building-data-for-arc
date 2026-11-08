from copy import deepcopy


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _is_rectangle(cells):
    r1, c1, r2, c2 = _bbox(cells)
    return len(cells) == (r2 - r1 + 1) * (c2 - c1 + 1)


def _components(grid):
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
            cells = set()
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def _largest_rectangle(cells):
    r1, c1, r2, c2 = _bbox(cells)
    best = set()
    for top in range(r1, r2 + 1):
        for bottom in range(top, r2 + 1):
            for left in range(c1, c2 + 1):
                for right in range(left, c2 + 1):
                    rectangle = {
                        (r, c)
                        for r in range(top, bottom + 1)
                        for c in range(left, right + 1)
                    }
                    if rectangle <= cells and len(rectangle) > len(best):
                        best = rectangle
    return best


def solve(grid):
    parts = _components(grid)
    target_color, target = next((color, cells) for color, cells in parts if _is_rectangle(cells))
    moving_color, creature = next((color, cells) for color, cells in parts if not _is_rectangle(cells))

    body = _largest_rectangle(creature)
    tail = creature - body
    br1, bc1, br2, bc2 = _bbox(body)
    tr1, tc1, tr2, tc2 = _bbox(target)

    if any(r < br1 for r, _ in tail):
        dr, dc = -1, 0
        steps = br1 - tr2 - 1
    elif any(r > br2 for r, _ in tail):
        dr, dc = 1, 0
        steps = tr1 - br2 - 1
    elif any(c < bc1 for _, c in tail):
        dr, dc = 0, -1
        steps = bc1 - tc2 - 1
    else:
        dr, dc = 0, 1
        steps = tc1 - bc2 - 1

    output = deepcopy(grid)
    for r, c in creature:
        output[r][c] = 0
    for r, c in body:
        output[r + dr * steps][c + dc * steps] = moving_color
    return output
